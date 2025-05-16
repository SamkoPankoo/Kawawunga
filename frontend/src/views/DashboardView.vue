<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card class="mb-6">
          <v-card-text>
            <div class="d-flex flex-wrap align-center">
              <div>
                <h1 class="text-h4">{{ $t('dashboard.welcome') }}, {{ user?.email }}</h1>
                <p class="text-subtitle-1 text-medium-emphasis">
                  {{ $t('dashboard.welcomeMessage') }}
                </p>
              </div>
              <v-spacer></v-spacer>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <!-- PDF History Component -->
        <PdfHistoryComponent />
      </v-col>

      <v-col cols="12" md="4">
        <v-card class="mb-6">
          <v-card-title>
            <v-icon start color="primary" class="mr-2">mdi-key</v-icon>
            {{ $t('dashboard.apiAccess') }}
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text>
            <p class="text-body-2 mb-4">{{ $t('dashboard.apiDescription') }}</p>

            <v-text-field
                v-model="apiKey"
                :label="$t('dashboard.apiKey')"
                readonly
                persistent-hint
                :hint="$t('dashboard.apiKeyHint')"
                bg-color="grey-lighten-4"
                class="mb-2"
            >
              <template v-slot:append>
                <v-tooltip :text="$t('dashboard.copyToClipboard')" location="top">
                  <template v-slot:activator="{ props }">
                    <v-btn
                        icon="mdi-content-copy"
                        variant="text"
                        density="comfortable"
                        v-bind="props"
                        @click="copyApiKey"
                    ></v-btn>
                  </template>
                </v-tooltip>
              </template>
            </v-text-field>

            <div class="d-flex">
              <v-spacer></v-spacer>
              <v-btn
                  @click="generateNewApiKey"
                  color="primary"
                  variant="outlined"
                  class="mt-2"
                  prepend-icon="mdi-refresh"
              >
                {{ $t('dashboard.generateNewKey') }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>

        <!-- Quick access -->
        <v-card>
          <v-card-title>
            <v-icon start color="primary" class="mr-2">mdi-lightning-bolt</v-icon>
            {{ $t('dashboard.quickAccess') }}
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-0">
            <v-list>
              <v-list-item
                  v-for="(feature, index) in quickFeatures"
                  :key="index"
                  :to="feature.route"
                  :prepend-icon="feature.icon"
                  :title="$t(feature.title)"
              ></v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar
        v-model="showSnackbar"
        :timeout="3000"
        color="success"
    >
      {{ snackbarText }}
    </v-snackbar>
  </v-container>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue';
import { useRouter } from 'vue-router';
import {useAuthStore} from '@/stores/auth';
import axios from 'axios';
import PdfHistoryComponent from '../views/PdfHistoryComponent.vue';

const router = useRouter();
const authStore = useAuthStore();

const user = computed(() => authStore.user);
const apiKey = ref('');
const showSnackbar = ref(false);
const snackbarText = ref('');

const quickFeatures = [
  {
    title: 'pdf.mergePdf',
    icon: 'mdi-file-link',
    route: '/editor/merge'
  },
  {
    title: 'pdf.splitPdf',
    icon: 'mdi-scissors-cutting',
    route: '/editor/split'
  },
  {
    title: 'pdf.rotatePdf',
    icon: 'mdi-rotate-right',
    route: '/editor/rotate'
  },
  {
    title: 'pdf.watermarkPdf',
    icon: 'mdi-format-color-highlight',
    route: '/editor/watermark'
  },
  {
    title: 'pdf.protectPdf',
    icon: 'mdi-lock',
    route: '/editor/protect'
  },
  {
    title: 'pdf.compressPdf',
    icon: 'mdi-zip-box',
    route: '/editor/compress'
  },

];

onMounted(async () => {
  await fetchUserData();
});

const fetchUserData = async () => {
  try {
    const response = await authStore.fetchUser();
    if (authStore.user) {
      apiKey.value = authStore.user.apiKey || '';
    }
  } catch (error) {
    console.error('Failed to fetch user data:', error);
  }
};

const generateNewApiKey = async () => {
  try {
    const response = await axios.post(
        `${import.meta.env.VITE_API_URL}/auth/generate-api-key`,
        {},
        {
          headers: {
            'Authorization': `Bearer ${authStore.token}`
          }
        }
    );

    apiKey.value = response.data.apiKey;
    showSnackbar.value = true;
    snackbarText.value = 'New API key generated successfully';
  } catch (error) {
    console.error('Failed to generate new API key:', error);
  }
};
async function ensureApiKeyExists() {
  if (!authStore.user?.apiKey) {
    console.log('No API key found, generating one...');

    try {
      const response = await axios.post(
          `${import.meta.env.VITE_API_URL}/auth/generate-api-key`,
          {},
          {
            headers: {
              'Authorization': `Bearer ${authStore.token}`
            }
          }
      );

      if (response.data.apiKey) {
        // Update our store with the new API key
        await authStore.fetchUser();
        console.log('API key generated successfully:', response.data.apiKey.substring(0, 10) + '...');

        showSnackbar.value = true;
        snackbarText.value = 'New API key generated successfully';

        return true;
      }
    } catch (error) {
      console.error('Failed to generate API key:', error);

      showSnackbar.value = true;
      snackbarText.value = 'Failed to generate API key: ' + (error.response?.data?.message || error.message);

      return false;
    }
  } else {
    console.log('API key already exists:', authStore.user.apiKey.substring(0, 10) + '...');
    return true;
  }
}

const copyApiKey = () => {
  if (!apiKey.value) return;

  navigator.clipboard.writeText(apiKey.value)
      .then(() => {
        showSnackbar.value = true;
        snackbarText.value = 'API key copied to clipboard';
      })
      .catch(err => {
        console.error('Could not copy API key: ', err);
      });
};
</script>