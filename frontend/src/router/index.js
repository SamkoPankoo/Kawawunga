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
        path: '/editor',
        name: 'editor',
        component: () => import('../views/EditorView.vue'),
        meta: { requiresAuth: true }
    },
    // Editor routes
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
    {
        path: '/editor/delete-pages',
        name: 'delete-pages',
        component: () => import('../views/DeletePagesView.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/editor/metadata',
        name: 'edit-metadata',
        component: () => import('../views/EditMetadataView.vue'),
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
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
    const isGuest = to.matched.some(record => record.meta.guest)

    if (requiresAuth && !authStore.isAuthenticated) {
        next('/login')
    } else if (isGuest && authStore.isAuthenticated) {
        next('/')
    } else {
        next()
    }
})

export default router