import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('../layouts/GuestLayout.vue'),
    children: [
      { path: '', name: 'home', component: () => import('../views/Home.vue') },
      { path: 'search', name: 'search', component: () => import('../views/Search.vue') },
    ],
  },
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { requiresAdmin: true },
    children: [
      { path: '', name: 'admin-dashboard', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'musics', name: 'admin-musics', component: () => import('../views/admin/Musics.vue') },
      { path: 'tags', name: 'admin-tags', component: () => import('../views/admin/Tags.vue') },
      { path: 'upload', name: 'admin-upload', component: () => import('../views/admin/Upload.vue') },
    ],
  },
  {
    path: '/auth/callback',
    name: 'auth-callback',
    component: () => import('../views/AuthCallback.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const isAdmin = localStorage.getItem('isAdmin') === '1'

  if (to.meta.requiresAdmin && (!token || !isAdmin)) {
    next('/')
  } else {
    next()
  }
})

export default router
