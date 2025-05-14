<template>
  <v-app-bar app color="primary" dark>
    <v-app-bar-title>
      <router-link to="/" class="text-white text-decoration-none">
        PDF Editor
      </router-link>
    </v-app-bar-title>

    <v-spacer></v-spacer>

    <LanguageSwitcher />

    <template v-if="!authStore.isAuthenticated">
      <v-btn text :to="{ name: 'login' }">
        {{ $t('common.login') }}
      </v-btn>
      <v-btn text :to="{ name: 'register' }">
        {{ $t('common.register') }}
      </v-btn>
    </template>

    <template v-else>
      <v-btn text :to="{ name: 'dashboard' }">
        {{ $t('common.dashboard') }}
      </v-btn>
      <v-btn text :to="{ name: 'editor' }">
        {{ $t('common.editor') }}
      </v-btn>
      <v-btn text :to="{ name: 'api-docs' }">
        {{ $t('common.apiDocs') }}
      </v-btn>
      <v-btn text @click="logout">
        {{ $t('common.logout') }}
      </v-btn>
    </template>
  </v-app-bar>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import LanguageSwitcher from './LanguageSwitcher.vue'


const router = useRouter()
const authStore = useAuthStore()

const logout = () => {
  authStore.logout()
  router.push('/')
}
</script>