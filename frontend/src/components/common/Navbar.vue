<template>
  <v-app-bar color="primary" dark>
    <!-- Mobile menu button (hamburger) - only shows on mobile -->
    <v-app-bar-nav-icon
        @click="drawer = !drawer"
        class="d-flex d-sm-none"
    ></v-app-bar-nav-icon>

    <v-app-bar-title>
      <router-link to="/" class="text-white text-decoration-none">
        Kawawunga PDF Editor
      </router-link>
    </v-app-bar-title>

    <v-spacer></v-spacer>

    <LanguageSwitcher />

    <!-- Desktop menu -->
    <div class="d-none d-sm-flex">
      <template v-if="!authStore.isAuthenticated">
        <v-btn text :to="{ name: 'login' }">
          {{ $t('common.login') }}
        </v-btn>
        <v-btn text :to="{ name: 'register' }">
          {{ $t('common.register') }}
        </v-btn>
      </template>

      <template v-else>
        <!-- Admin sekcia -->
        <template v-if="authStore.isAdmin">
          <v-btn text :to="{ name: 'admin-dashboard' }">
            {{ $t('common.adminDashboard') }}
          </v-btn>
        </template>

        <!-- Sekcia pre bežných používateľov (aj admin má tieto tlačidlá) -->
        <v-btn text :to="{ name: 'dashboard' }">
          {{ $t('common.dashboard') }}
        </v-btn>
        <v-btn text :to="{ name: 'editor' }">
          {{ $t('common.editor') }}
        </v-btn>
        <v-btn text :to="{ name: 'user-guide' }">
          {{ $t('common.userGuide') }}
        </v-btn>
        <v-btn text :to="{ name: 'api-docs' }">
          {{ $t('common.apiDocs') }}
        </v-btn>
        <v-btn text @click="logout">
          {{ $t('common.logout') }}
        </v-btn>
      </template>
    </div>
  </v-app-bar>

  <!-- Navigation drawer for mobile -->
  <v-navigation-drawer
      v-model="drawer"
      temporary
      location="left"
  >
    <v-list>
      <v-list-item :to="{ name: 'home' }">
        <template v-slot:prepend>
          <v-icon>mdi-home</v-icon>
        </template>
        {{ $t('common.home') }}
      </v-list-item>

      <template v-if="!authStore.isAuthenticated">
        <v-list-item :to="{ name: 'login' }">
          <template v-slot:prepend>
            <v-icon>mdi-login</v-icon>
          </template>
          {{ $t('common.login') }}
        </v-list-item>
        <v-list-item :to="{ name: 'register' }">
          <template v-slot:prepend>
            <v-icon>mdi-account-plus</v-icon>
          </template>
          {{ $t('common.register') }}
        </v-list-item>
      </template>

      <template v-else>
        <!-- Admin section -->
        <template v-if="authStore.isAdmin">
          <v-list-item :to="{ name: 'admin-dashboard' }">
            <template v-slot:prepend>
              <v-icon>mdi-view-dashboard</v-icon>
            </template>
            {{ $t('common.adminDashboard') }}
          </v-list-item>
        </template>

        <!-- User section -->
        <v-list-item :to="{ name: 'dashboard' }">
          <template v-slot:prepend>
            <v-icon>mdi-view-dashboard</v-icon>
          </template>
          {{ $t('common.dashboard') }}
        </v-list-item>
        <v-list-item :to="{ name: 'editor' }">
          <template v-slot:prepend>
            <v-icon>mdi-file-pdf-box</v-icon>
          </template>
          {{ $t('common.editor') }}
        </v-list-item>
        <v-list-item :to="{ name: 'user-guide' }">
          <template v-slot:prepend>
            <v-icon>mdi-book</v-icon>
          </template>
          {{ $t('common.userGuide') }}
        </v-list-item>
        <v-list-item :to="{ name: 'api-docs' }">
          <template v-slot:prepend>
            <v-icon>mdi-api</v-icon>
          </template>
          {{ $t('common.apiDocs') }}
        </v-list-item>
        <v-divider></v-divider>
        <v-list-item @click="logout">
          <template v-slot:prepend>
            <v-icon>mdi-logout</v-icon>
          </template>
          {{ $t('common.logout') }}
        </v-list-item>
      </template>
    </v-list>
  </v-navigation-drawer>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/stores/auth.js';
import LanguageSwitcher from './LanguageSwitcher.vue';

const router = useRouter();
const authStore = useAuthStore();
const drawer = ref(false);

const logout = () => {
  drawer.value = false; // Close the drawer if it's open
  authStore.logout();
  router.push('/');
};
</script>