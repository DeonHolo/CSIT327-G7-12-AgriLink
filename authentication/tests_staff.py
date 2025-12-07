"""
Tests for staff dashboard views, verification actions, and audit logging.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import AuditLog
from products.models import Product, Category

User = get_user_model()


class StaffAccessTestCase(TestCase):
    """Tests for staff-only access control."""
    
    def setUp(self):
        self.client = Client()
        self.regular_user = User.objects.create_user(
            username='regular',
            email='regular@test.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
    
    def test_staff_dashboard_requires_staff(self):
        """Non-staff users should be redirected from staff dashboard."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('staff_dashboard'))
        self.assertNotEqual(response.status_code, 200)
    
    def test_staff_dashboard_accessible_to_staff(self):
        """Staff users should access the dashboard."""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(reverse('staff_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_verification_list_requires_staff(self):
        """Non-staff users should be redirected from verification list."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('staff_verification_list'))
        self.assertNotEqual(response.status_code, 200)
    
    def test_products_list_requires_staff(self):
        """Non-staff users should be redirected from products list."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('staff_products_list'))
        self.assertNotEqual(response.status_code, 200)
    
    def test_users_list_requires_staff(self):
        """Non-staff users should be redirected from users list."""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(reverse('staff_users_list'))
        self.assertNotEqual(response.status_code, 200)


class VerificationActionsTestCase(TestCase):
    """Tests for farmer verification workflow."""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        self.pending_user = User.objects.create_user(
            username='pending',
            email='pending@test.com',
            password='testpass123',
            user_type='buyer',
            business_permit_status='pending'
        )
        self.client.login(username='staff', password='testpass123')
    
    def test_approve_verification(self):
        """Test approving a farmer verification request."""
        response = self.client.post(
            reverse('staff_verification_action', args=[self.pending_user.pk]),
            {'action': 'approve', 'notes': 'Approved - valid permit'}
        )
        
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.business_permit_status, 'approved')
        self.assertEqual(self.pending_user.user_type, 'farmer')
        
        # Check audit log created
        audit = AuditLog.objects.filter(
            target_user=self.pending_user,
            action='verification_approve'
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.actor, self.staff_user)
    
    def test_reject_verification_requires_notes(self):
        """Rejecting verification should require notes."""
        response = self.client.post(
            reverse('staff_verification_action', args=[self.pending_user.pk]),
            {'action': 'reject', 'notes': ''}
        )
        
        self.pending_user.refresh_from_db()
        # Status should remain pending since notes are required
        self.assertEqual(self.pending_user.business_permit_status, 'pending')
    
    def test_reject_verification_with_notes(self):
        """Test rejecting a farmer verification request with notes."""
        response = self.client.post(
            reverse('staff_verification_action', args=[self.pending_user.pk]),
            {'action': 'reject', 'notes': 'Invalid document - blurry image'}
        )
        
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.business_permit_status, 'rejected')
        self.assertEqual(self.pending_user.business_permit_notes, 'Invalid document - blurry image')
        
        # Check audit log
        audit = AuditLog.objects.filter(
            target_user=self.pending_user,
            action='verification_reject'
        ).first()
        self.assertIsNotNone(audit)
    
    def test_request_reupload(self):
        """Test requesting document reupload."""
        response = self.client.post(
            reverse('staff_verification_action', args=[self.pending_user.pk]),
            {'action': 'reupload', 'notes': 'Please upload a clearer image'}
        )
        
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.business_permit_status, 'none')
        
        # Check audit log
        audit = AuditLog.objects.filter(
            target_user=self.pending_user,
            action='verification_reupload'
        ).first()
        self.assertIsNotNone(audit)
    
    def test_reset_to_pending(self):
        """Test resetting status back to pending."""
        # First approve
        self.pending_user.business_permit_status = 'approved'
        self.pending_user.save()
        
        response = self.client.post(
            reverse('staff_verification_action', args=[self.pending_user.pk]),
            {'action': 'reset', 'notes': 'Re-reviewing application'}
        )
        
        self.pending_user.refresh_from_db()
        self.assertEqual(self.pending_user.business_permit_status, 'pending')


class ProductModerationTestCase(TestCase):
    """Tests for product moderation actions."""
    
    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        self.farmer = User.objects.create_user(
            username='farmer',
            email='farmer@test.com',
            password='testpass123',
            user_type='farmer'
        )
        self.category = Category.objects.create(name='Vegetables')
        self.product = Product.objects.create(
            farmer=self.farmer,
            name='Test Tomatoes',
            category=self.category,
            description='Fresh tomatoes',
            price=50.00,
            unit='kg',
            stock_quantity=100,
            is_active=True
        )
        self.client.login(username='staff', password='testpass123')
    
    def test_unlist_product_requires_notes(self):
        """Unlisting a product should require notes."""
        response = self.client.post(
            reverse('staff_product_action', args=[self.product.pk]),
            {'action': 'unlist', 'notes': ''}
        )
        
        self.product.refresh_from_db()
        # Product should still be active since notes are required
        self.assertTrue(self.product.is_active)
    
    def test_unlist_product_with_notes(self):
        """Test unlisting a product with notes."""
        response = self.client.post(
            reverse('staff_product_action', args=[self.product.pk]),
            {'action': 'unlist', 'notes': 'Inappropriate content'}
        )
        
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_active)
        
        # Check audit log
        audit = AuditLog.objects.filter(
            target_product=self.product,
            action='product_unlist'
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.notes, 'Inappropriate content')
    
    def test_restore_product(self):
        """Test restoring an unlisted product."""
        self.product.is_active = False
        self.product.save()
        
        response = self.client.post(
            reverse('staff_product_action', args=[self.product.pk]),
            {'action': 'restore', 'notes': ''}
        )
        
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)
        
        # Check audit log
        audit = AuditLog.objects.filter(
            target_product=self.product,
            action='product_restore'
        ).first()
        self.assertIsNotNone(audit)
    
    def test_feature_product(self):
        """Test featuring a product."""
        response = self.client.post(
            reverse('staff_product_action', args=[self.product.pk]),
            {'action': 'feature', 'notes': ''}
        )
        
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_featured)
        
        # Check audit log
        audit = AuditLog.objects.filter(
            target_product=self.product,
            action='product_feature'
        ).first()
        self.assertIsNotNone(audit)
    
    def test_bulk_unlist(self):
        """Test bulk unlisting products."""
        product2 = Product.objects.create(
            farmer=self.farmer,
            name='Test Carrots',
            category=self.category,
            description='Fresh carrots',
            price=40.00,
            unit='kg',
            stock_quantity=50,
            is_active=True
        )
        
        response = self.client.post(
            reverse('staff_products_bulk_action'),
            {
                'bulk_action': 'unlist',
                'product_ids': [self.product.pk, product2.pk],
                'notes': 'Bulk moderation'
            }
        )
        
        self.product.refresh_from_db()
        product2.refresh_from_db()
        
        self.assertFalse(self.product.is_active)
        self.assertFalse(product2.is_active)
        
        # Check audit logs created for both
        audits = AuditLog.objects.filter(action='product_unlist').count()
        self.assertEqual(audits, 2)


class UserManagementTestCase(TestCase):
    """Tests for user management actions."""
    
    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@test.com',
            password='testpass123'
        )
        self.target_user = User.objects.create_user(
            username='target',
            email='target@test.com',
            password='testpass123',
            user_type='buyer'
        )
        self.client.login(username='admin', password='testpass123')
    
    def test_set_role_to_farmer(self):
        """Test changing user role to farmer."""
        response = self.client.post(
            reverse('staff_user_action', args=[self.target_user.pk]),
            {'action': 'set_farmer', 'notes': 'Manual role change'}
        )
        
        self.target_user.refresh_from_db()
        self.assertEqual(self.target_user.user_type, 'farmer')
        
        # Check audit log
        audit = AuditLog.objects.filter(
            target_user=self.target_user,
            action='user_role_change'
        ).first()
        self.assertIsNotNone(audit)
    
    def test_deactivate_user(self):
        """Test deactivating a user account."""
        response = self.client.post(
            reverse('staff_user_action', args=[self.target_user.pk]),
            {'action': 'deactivate', 'notes': 'Terms violation'}
        )
        
        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)
        
        # Check audit log
        audit = AuditLog.objects.filter(
            target_user=self.target_user,
            action='user_deactivate'
        ).first()
        self.assertIsNotNone(audit)
    
    def test_reactivate_user(self):
        """Test reactivating a user account."""
        self.target_user.is_active = False
        self.target_user.save()
        
        response = self.client.post(
            reverse('staff_user_action', args=[self.target_user.pk]),
            {'action': 'reactivate', 'notes': ''}
        )
        
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_active)
    
    def test_promote_to_staff_requires_superuser(self):
        """Only superusers should be able to promote to staff."""
        staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        
        # Login as regular staff (not superuser)
        self.client.login(username='staff', password='testpass123')
        
        response = self.client.post(
            reverse('staff_user_action', args=[self.target_user.pk]),
            {'action': 'set_staff', 'notes': ''}
        )
        
        self.target_user.refresh_from_db()
        # Should still not be staff
        self.assertFalse(self.target_user.is_staff)
    
    def test_superuser_can_promote_to_staff(self):
        """Superusers should be able to promote to staff."""
        response = self.client.post(
            reverse('staff_user_action', args=[self.target_user.pk]),
            {'action': 'set_staff', 'notes': 'Promoted to help with moderation'}
        )
        
        self.target_user.refresh_from_db()
        self.assertTrue(self.target_user.is_staff)


class AuditLogTestCase(TestCase):
    """Tests for audit log model and functionality."""
    
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123',
            is_staff=True
        )
        self.target_user = User.objects.create_user(
            username='target',
            email='target@test.com',
            password='testpass123'
        )
    
    def test_audit_log_creation(self):
        """Test creating an audit log entry."""
        audit = AuditLog.objects.create(
            actor=self.staff_user,
            action='verification_approve',
            target_user=self.target_user,
            previous_status='pending',
            new_status='approved',
            notes='Test approval'
        )
        
        self.assertIsNotNone(audit.created_at)
        self.assertEqual(audit.actor, self.staff_user)
        self.assertEqual(audit.get_action_display(), 'Approved Verification')
    
    def test_audit_log_ordering(self):
        """Audit logs should be ordered by created_at descending."""
        AuditLog.objects.create(
            actor=self.staff_user,
            action='verification_approve',
            target_user=self.target_user
        )
        AuditLog.objects.create(
            actor=self.staff_user,
            action='verification_reject',
            target_user=self.target_user
        )
        
        audits = list(AuditLog.objects.all())
        # Most recent (reject) should be first
        self.assertEqual(audits[0].action, 'verification_reject')
        self.assertEqual(audits[1].action, 'verification_approve')
