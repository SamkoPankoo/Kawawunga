<template>
  <v-app>
    <Navbar />
    <v-main>
      <router-view />
    </v-main>
    <CookieConsent />
  </v-app>
</template>

<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import Navbar from './components/common/Navbar.vue'
import CookieConsent from './components/common/CookieConsent.vue'

const authStore = useAuthStore()

onMounted(() => {
  if (authStore.isAuthenticated) {
    authStore.fetchUser()
  }
})
</script>
<style>
body {
  font-family: 'Poppins', sans-serif;
}

.v-application {
  font-family: 'Poppins', sans-serif !important;
}

/* Add a nice box shadow to cards for better depth */
.v-card {
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
  transition: transform 0.2s, box-shadow 0.2s;
}

.v-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15) !important;
}

/* Make buttons more attractive */
.v-btn {
  text-transform: none !important;
  letter-spacing: 0.5px;
  font-weight: 500;
}
</style>