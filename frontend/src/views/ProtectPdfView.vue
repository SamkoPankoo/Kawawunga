<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.protectPdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.protectPdfDesc') }}</p>

            <v-file-input
                v-model="selectedFile"
                :label="$t('pdf.dropFilesHere')"
                accept="application/pdf"
                prepend-icon="mdi-file-pdf-box"
                :rules="[rules.required]"
                @update:model-value="handleFileChange"
                counter
                show-size
            ></v-file-input>

            <v-alert
                v-if="error"
                type="error"
                variant="tonal"
                class="mb-4"
                closable
            >
              {{ error }}
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row v-if="pdfInfo">
      <v-col cols="12" md="7">
        <v-card>
          <v-card-title>{{ $t('pdf.preview') }}</v-card-title>
          <v-card-text>
            <pdf
                v-if="pdfUrl"
                :src="pdfUrl"
                :page="currentPage"
                @num-pages="numPages = $event"
                @page-loaded="pageLoaded"
                @error="handleError"
                style="display: block; width: 100%;"
            ></pdf>
            <v-progress-circular
                v-if="loading"
                indeterminate
                color="primary"
                class="mt-5"
            ></v-progress-circular>

            <div class="d-flex justify-center align-center mt-4">
              <v-btn icon="mdi-chevron-left" @click="prevPage" :disabled="currentPage <= 1"></v-btn>
              <span class="mx-2">{{ currentPage }} / {{ numPages }}</span>
              <v-btn icon="mdi-chevron-right" @click="nextPage" :disabled="currentPage >= numPages"></v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card>
          <v-card-title>{{ $t('pdf.protectOptions') }}</v-card-title>
          <v-card-text>
            <v-text-field
                v-model="userPassword"
                :label="$t('pdf.password')"
                :rules="[rules.required]"
                :type="showPassword ? 'text' : 'password'"
                :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append="showPassword = !showPassword"
                class="mb-2"
            ></v-text-field>

            <v-text-field
                v-model="confirmPassword"
                :label="$t('pdf.confirmPassword')"
                :rules="[rules.required, validatePasswordMatch]"
                :type="showPassword ? 'text' : 'password'"
                class="mb-4"
            ></v-text-field>

            <v-text-field
                v-model="ownerPassword"
                :label="$t('pdf.ownerPassword')"
                :hint="$t('pdf.ownerPasswordHint')"
                persistent-hint
                :type="showPassword ? 'text' : 'password'"
                class="mb-4"
            ></v-text-field>

            <v-divider class="my-4"></v-divider>

            <h3 class="text-subtitle-1 font-weight-bold mb-2">{{ $t('pdf.permissions') }}</h3>
            <v-switch
                v-model="allowPrinting"
                :label="$t('pdf.allowPrinting')"
                class="mb-2"
            ></v-switch>
            <v-switch
                v-model="allowCopying"
                :label="$t('pdf.allowCopying')"
                class="mb-2"
            ></v-switch>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canProtect || processing"
                :loading="processing"
                @click="protectPdf"
                prepend-icon="mdi-lock"
                size="large"
            >
              {{ $t('pdf.applyProtection') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-dialog v-model="showResultDialog" max-width="500">
      <v-card>
        <v-card-title class="text-h5">
          <v-icon color="success" class="mr-2">mdi-check-circle</v-icon>
          {{ $t('common.success') }}
        </v-card-title>
        <v-card-text>
          <p>{{ $t('pdf.protectionApplied') }}</p>
          <p class="text-grey">{{ resultFilename }}</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
              color="primary"
              variant="text"
              @click="showResultDialog = false"
          >
            {{ $t('common.close') }}
          </v-btn>
          <v-btn
              color="primary"
              @click="downloadResult"
              prepend-icon="mdi-download"
          >
            {{ $t('common.download') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import PdfEmbed from 'vue-pdf-embed';
import { useAuthStore } from '../stores/auth';

const { t } = useI18n();
const authStore = useAuthStore();

const selectedFile = ref(null);
const pdfUrl = ref(null);
const pdfInfo = ref(null);
const currentPage = ref(1);
const numPages = ref(0);
const loading = ref(false);
const error = ref(null);
const fileId = ref(null);

// Protection options
const userPassword = ref('');
const confirmPassword = ref('');
const ownerPassword = ref('');
const showPassword = ref(false);
const allowPrinting = ref(true);
const allowCopying = ref(true);
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);

const rules = {
  required: value => !!value || t('validation.required')
};

const validatePasswordMatch = () => {
  return userPassword.value === confirmPassword.value || t('validation.passwordMatch');
};

const canProtect = computed(() => {
  return pdfInfo.value &&
      userPassword.value &&
      userPassword.value === confirmPassword.value;
});

const handleFileChange = () => {
  if (selectedFile.value) {
    pdfUrl.value = URL.createObjectURL(selectedFile.value);
    uploadFile();
  } else {
    pdfUrl.value = null;
    pdfInfo.value = null;
    fileId.value = null;
  }
};

const pageLoaded = () => {
  loading.value = false;
};

const handleError = (err) => {
  console.error('PDF error:', err);
  loading.value = false;
};

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
    loading.value = true;
  }
};

const nextPage = () => {
  if (currentPage.value < numPages.value) {
    currentPage.value++;
    loading.value = true;
  }
};

const uploadFile = async () => {
  if (!selectedFile.value) return;

  loading.value = true;
  error.value = null;

  try {
    const formData = new FormData();
    formData.append('pdf', selectedFile.value);

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/upload`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
    );

    fileId.value = response.data.id;
    pdfInfo.value = response.data;
  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};

const protectPdf = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    const requestData = {
      file_id: fileId.value,
      user_password: userPassword.value,
      owner_password: ownerPassword.value || userPassword.value,
      allow_printing: allowPrinting.value,
      allow_copying: allowCopying.value
    };

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/protect`,
        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;
    resultFilename.value = response.data.filename || 'protected.pdf';
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error protecting PDF:', error);
    error.value = error.response?.data?.error || t('pdf.protectError');
  } finally {
    processing.value = false;
  }
};

const downloadResult = async () => {
  if (!resultFileUrl.value) return;

  try {
    const response = await axios.get(
        `${import.meta.env.VITE_PYTHON_API_URL}/download/${resultFileUrl.value}`,
        { responseType: 'blob' }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', resultFilename.value);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error downloading file:', error);
    error.value = t('pdf.downloadError');
  }
};
</script>