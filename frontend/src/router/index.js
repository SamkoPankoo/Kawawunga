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
    {
        path: '/user-guide',
        name: 'user-guide',
        component: () => import('../views/UserGuideView.vue'),
        meta: { requiresAuth: false }
    },
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
    },
]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes
})

router.beforeEach((to, from, next) => {
    // Get auth store in a way that avoids the double-click issue
    const authStore = useAuthStore()

    // Route requires auth
    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!authStore.isAuthenticated) {
            next('/login')
            return
        }

        // Admin check
        if (to.matched.some(record => record.meta.requiresAdmin) && !authStore.isAdmin) {
            next('/dashboard')
            return
        }

        // User is authenticated - proceed to route
        next()

        // Fetch user data in background if needed
        if (!authStore.user) {
            authStore.fetchUser().catch(err => console.error('Background fetch failed:', err))
        }
    }
    // Guest routes
    else if (to.matched.some(record => record.meta.guest) && authStore.isAuthenticated) {
        next('/dashboard')
    }
    // Public routes
    else {
        next()
    }
})

export default router