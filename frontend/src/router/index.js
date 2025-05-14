import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
    {
        path: '/',
        name: 'home',
        component: () => import('../views/HomeView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/admin-dashboard',
        name: 'admin-dashboard',
        component: () => import('../views/AdminDashboardView.vue'),
        meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
        path: '/login',
        name: 'login',
        component: () => import('../views/LoginView.vue'),
        meta: { guest: true }
    },
    {
        path: '/register',
        name: 'register',
        component: () => import('../views/RegisterView.vue'),
        meta: { guest: true }
    },
    {
        path: '/dashboard',
        name: 'dashboard',
        component: () => import('../views/DashboardView.vue'),
        meta: { requiresAuth: true }
    },
    // Používateľská príručka
    {
        path: '/user-guide',
        name: 'user-guide',
        component: () => import('../views/UserGuideView.vue'),
        meta: { requiresAuth: false }
    },
    // API dokumentácia
    {
        path: '/api-docs',
        name: 'api-docs',
        component: () => import('../views/ApiDocsView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor',
        name: 'editor',
        component: () => import('../views/EditorView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/merge',
        name: 'merge-pdf',
        component: () => import('../views/MergePdfView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/rotate',
        name: 'rotate-pdf',
        component: () => import('../views/RotatePdfView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/split',
        name: 'split-pdf',
        component: () => import('../views/SplitPdfView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/watermark',
        name: 'watermark-pdf',
        component: () => import('../views/WatermarkPdfView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/delete-pages',
        name: 'delete-pages',
        component: () => import('../views/DeletePagesView.vue'),
        meta: { requiresAuth: true }
    },
    // New editor routes
    {
        path: '/editor/protect',
        name: 'protect-pdf',
        component: () => import('../views/ProtectPdfView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/compress',
        name: 'compress-pdf',
        component: () => import('../views/CompressPdfView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/metadata',
        name: 'edit-metadata',
        component: () => import('../views/EditMetadataView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/image-to-pdf',
        name: 'image-to-pdf',
        component: () => import('../views/ImageToPdfView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/pdf-to-image',
        name: 'pdf-to-image',
        component: () => import('../views/PdfToImageView.vue'),
        meta: { requiresAuth: true }
    }



]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
})

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore();

    if (to.matched.some(record => record.meta.requiresAuth)) {
        // For routes requiring auth
        if (!authStore.isAuthenticated) {
            // If not authenticated, redirect to login
            next('/login');
        } else if (to.matched.some(record => record.meta.requiresAdmin) && !authStore.isAdmin) {
            // If route requires admin privileges but user is not admin
            next('/dashboard');
        } else {
            // Otherwise proceed
            next();
        }
    } else if (to.matched.some(record => record.meta.guest)) {
        // For guest-only routes (like login/register)
        if (authStore.isAuthenticated) {
            next('/dashboard');
        } else {
            next();
        }
    } else {
        // For public routes
        next();
    }
});

export default router