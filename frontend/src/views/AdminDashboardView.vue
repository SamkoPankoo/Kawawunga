// src/views/AdminDashboardView.vue
<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <div>
              <v-icon start color="primary" class="mr-2">mdi-view-dashboard</v-icon>
              {{ $t('admin.adminWelcome') }}
            </div>
          </v-card-title>
          <v-card-text>
            <p>{{ $t('admin.adminWelcomeMessage') }}</p>
            <v-btn color="primary" @click="refreshData" class="mt-4">
              {{ $t('admin.refreshData') }}
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <AdminHistoryComponent />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth';
import AdminHistoryComponent from '@/components/admin/AdminHistoryComponent.vue';
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';

const authStore = useAuthStore();
const router = useRouter();

// On component mount, check if user is admin
onMounted(() => {
  if (!authStore.isAuthenticated) {
    console.log('Not authenticated, redirecting to login');
    router.push('/login');
    return;
  }

  if (!authStore.isAdmin) {
    console.log('Not admin, redirecting to dashboard');
    router.push('/dashboard');
    return;
  }

  console.log('Admin dashboard loaded for user:', authStore.user?.email);
});

const refreshData = () => {
  // Refresh auth state first
  authStore.fetchUser().then(() => {
    // Force refresh of child components
    const event = new CustomEvent('refresh-admin-data');
    window.dispatchEvent(event);
  });
};
</script>