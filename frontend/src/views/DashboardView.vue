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
              <v-btn
                  color="primary"
                  class="ml-2 mt-2"
                  prepend-icon="mdi-folder-plus"
                  :to="{ name: 'home' }"
              >
                {{ $t('dashboard.newProject') }}
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <v-card class="mb-6">
          <v-card-title>
            <v-icon start color="primary" class="mr-2">mdi-clock-outline</v-icon>
            {{ $t('dashboard.recentActivity') }}
          </v-card-title>
          <v-divider></v-divider>
          <v-card-text class="pa-0">
            <v-list lines="two">
              <v-list-item
                  v-for="(activity, index) in recentActivities"
                  :key="index"
                  :title="activity.title"
                  :subtitle="activity.date"
              >
                <template v-slot:prepend>
                  <v-avatar color="grey-lighten-3">
                    <v-icon :color="activity.iconColor">{{ activity.icon }}</v-icon>
                  </v-avatar>
                </template>
                <template v-slot:append>
                  <v-btn
                      variant="text"
                      size="small"
                      color="primary"
                      @click="openFile(activity)"
                  >
                    {{ $t('dashboard.open') }}
                  </v-btn>
                </template>
              </v-list-item>

              <div v-if="recentActivities.length === 0" class="pa-4 text-center">
                <v-icon size="64" color="grey-lighten-2" class="mb-2">mdi-file-outline</v-icon>
                <p>{{ $t('dashboard.noActivity') }}</p>
              </div>
            </v-list>
          </v-card-text>
        </v-card>
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
import { useAuthStore } from '../stores/auth';
import axios from 'axios';

const router = useRouter();
const authStore = useAuthStore();

const user = computed(() => authStore.user);
const apiKey = ref('');
const showSnackbar = ref(false);
const snackbarText = ref('');

// Mock data - v reálnej aplikácii by ste tieto dáta získali z API
const recentActivities = ref([
  {
    title: 'merged_2_files.pdf',
    date: '10 minút',
    icon: 'mdi-file-link',
    iconColor: 'blue',
    type: 'merge'
  },
  {
    title: 'extracted_pages_1-3-5.pdf',
    date: '2 hodiny',
    icon: 'mdi-file-split',
    iconColor: 'orange',
    type: 'split'
  },
  {
    title: 'rotated.pdf',
    date: 'včera',
    icon: 'mdi-rotate-right',
    iconColor: 'green',
    type: 'rotate'
  }
]);

const quickFeatures = [
  {
    title: 'pdf.mergePdf',
    icon: 'mdi-file-link',
    route: '/editor/merge'
  },
  {
    title: 'pdf.splitPdf',
    icon: 'mdi-file-split',
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
  }
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
    snackbarText.value = 'Nový API kľúč bol vygenerovaný';
  } catch (error) {
    console.error('Failed to generate new API key:', error);
  }
};

const copyApiKey = () => {
  if (!apiKey.value) return;

  navigator.clipboard.writeText(apiKey.value)
      .then(() => {
        showSnackbar.value = true;
        snackbarText.value = 'API kľúč skopírovaný do schránky';
      })
      .catch(err => {
        console.error('Could not copy API key: ', err);
      });
};

const openFile = (activity) => {
  // Tu by sa mal otvoriť súbor na základe typu aktivity
  // V reálnej aplikácii by ste presmerovali na príslušný editor s ID súboru
  router.push({ name: activity.type + '-pdf' });
};
</script>