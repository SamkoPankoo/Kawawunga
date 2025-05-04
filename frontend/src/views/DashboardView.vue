<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">{{ $t('common.dashboard') }}</h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>{{ $t('dashboard.recentFiles') }}</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item
                  v-for="file in recentFiles"
                  :key="file.id"
                  @click="openFile(file)"
              >
                <template v-slot:prepend>
                  <v-icon>mdi-file-pdf-box</v-icon>
                </template>
                <v-list-item-title>{{ file.name }}</v-list-item-title>
                <v-list-item-subtitle>{{ formatDate(file.updatedAt) }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>{{ $t('dashboard.quickActions') }}</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item :to="{ name: 'editor' }">
                <template v-slot:prepend>
                  <v-icon>mdi-file-document-edit</v-icon>
                </template>
                <v-list-item-title>{{ $t('dashboard.newDocument') }}</v-list-item-title>
              </v-list-item>

              <v-list-item v-if="authStore.isAdmin" :to="{ name: 'admin' }">
                <template v-slot:prepend>
                  <v-icon>mdi-shield-account</v-icon>
                </template>
                <v-list-item-title>{{ $t('dashboard.adminPanel') }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>{{ $t('dashboard.apiAccess') }}</v-card-title>
          <v-card-text>
            <v-text-field
                v-model="apiKey"
                :label="$t('dashboard.apiKey')"
                readonly
                append-icon="mdi-content-copy"
                @click:append="copyApiKey"
            />
            <v-btn @click="generateNewApiKey" color="primary">
              {{ $t('dashboard.generateNewKey') }}
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../services/api'

const router = useRouter()
const authStore = useAuthStore()

const recentFiles = ref([])
const apiKey = ref('')

onMounted(async () => {
  await fetchUserData()
})

const fetchUserData = async () => {
  try {
    const response = await api.get('/auth/me')
    apiKey.value = response.data.apiKey
  } catch (error) {
    console.error('Failed to fetch user data:', error)
  }
}

const generateNewApiKey = async () => {
  try {
    const response = await api.post('/auth/generate-api-key')
    apiKey.value = response.data.apiKey
  } catch (error) {
    console.error('Failed to generate new API key:', error)
  }
}

const copyApiKey = () => {
  navigator.clipboard.writeText(apiKey.value)
}

const formatDate = (date) => {
  return new Date(date).toLocaleDateString()
}

const openFile = (file) => {
  router.push({ name: 'editor', params: { id: file.id } })
}
</script>