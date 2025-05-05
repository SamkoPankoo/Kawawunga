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
    // Pridaná chýbajúca "editor" routa
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
        path: '/editor/delete-pages',
        name: 'delete-pages',
        component: () => import('../views/DeletePagesView.vue'),
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const authStore = useAuthStore()

    if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!authStore.isAuthenticated) {
            next('/login')
        } else {
            next()
        }
    } else if (to.matched.some(record => record.meta.guest)) {
        if (authStore.isAuthenticated) {
            next('/')
        } else {
            next()
        }
    } else {
        next()
    }
})

export default router