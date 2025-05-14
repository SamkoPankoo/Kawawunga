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

          <v-card-title class="d-flex align-center">
            <span>{{ $t('pdf.preview') }}</span>
            <v-spacer></v-spacer>
            <v-chip v-if="isPreviewProtected" color="success" size="small" class="ml-2">
              {{ $t('pdf.previewProtected') }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <vue-pdf-embed
                v-if="currentPreviewUrl"
                :source="currentPreviewUrl"
                :page="currentPage"
                @loaded="numPages = $event.numPages"
                @rendered="pageLoaded"
                @error="handleError"
                style="display: block; width: 100%;"
            ></vue-pdf-embed>

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

                @update:model-value="previewProtection"

            ></v-text-field>

            <v-text-field
                v-model="confirmPassword"
                :label="$t('pdf.confirmPassword')"
                :rules="[rules.required, validatePasswordMatch]"
                :type="showPassword ? 'text' : 'password'"
                class="mb-4"

                @update:model-value="previewProtection"

            ></v-text-field>

            <v-text-field
                v-model="ownerPassword"
                :label="$t('pdf.ownerPassword')"
                :hint="$t('pdf.ownerPasswordHint')"
                persistent-hint
                :type="showPassword ? 'text' : 'password'"
                class="mb-4"

                @update:model-value="previewProtection"

            ></v-text-field>

            <v-divider class="my-4"></v-divider>

            <h3 class="text-subtitle-1 font-weight-bold mb-2">{{ $t('pdf.permissions') }}</h3>
            <v-switch
                v-model="allowPrinting"
                :label="$t('pdf.allowPrinting')"
                class="mb-2"

                @update:model-value="previewProtection"

            ></v-switch>
            <v-switch
                v-model="allowCopying"
                :label="$t('pdf.allowCopying')"
                class="mb-2"

                @update:model-value="previewProtection"
            ></v-switch>

            <v-alert
                v-if="isPreviewProtected"
                type="info"
                variant="tonal"
                class="mt-4"
            >
              {{ $t('pdf.previewPasswordInfo') }}
            </v-alert>

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

    <LogOperation
        v-if="operationSuccess"
        :operation="'protect'"
        :description="getLogDescription()"
        :metadata="getLogMetadata()"

    />

  </v-container>
</template>

<script setup>

import { ref, computed, watch, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import VuePdfEmbed from 'vue-pdf-embed';
import {useAuthStore} from '@/stores/auth';
import LogOperation from '@/components/pdf/LogOperation.vue';
const operationSuccess = ref(false);
const resultFileId = ref(null);


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


// For live preview
const previewPdfUrl = ref(null);
const isPreviewProtected = ref(false);
const previewPending = ref(false);
const previewTimeout = ref(null);

// Current preview that's being displayed
const currentPreviewUrl = computed(() => {
  return previewPdfUrl.value || pdfUrl.value;
});


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


const getLogDescription = () => {
  return `Protected PDF with password (${allowPrinting.value ? 'printing allowed' : 'printing disabled'}, ${allowCopying.value ? 'copying allowed' : 'copying disabled'})`;
};

const getLogMetadata = () => {
  return {
    fileName: selectedFile.value?.name,
    protectionOptions: {
      allowPrinting: allowPrinting.value,
      allowCopying: allowCopying.value
    },
    resultFile: resultFilename.value,
    timestamp: new Date().toISOString()
  };
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

    // Reset preview when changing file
    previewPdfUrl.value = null;
    isPreviewProtected.value = false;
    uploadFile();
  } else {
    pdfUrl.value = null;
    previewPdfUrl.value = null;
    pdfInfo.value = null;
    fileId.value = null;
    isPreviewProtected.value = false;

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

        `/python-api/upload`,

        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
    );

    fileId.value = response.data.id;
    pdfInfo.value = response.data;


    // Initial preview after upload
    if (userPassword.value && userPassword.value === confirmPassword.value) {
      previewProtection();
    }

  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};


// Function to create live preview of protection
const previewProtection = () => {
  // Debounce preview requests
  if (previewTimeout.value) {
    clearTimeout(previewTimeout.value);
  }

  previewTimeout.value = setTimeout(async () => {
    if (!fileId.value || previewPending.value) return;

    // Only preview if we have valid protection settings
    if (!canProtect.value) {
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewProtected.value = false;
      }
      return;
    }

    previewPending.value = true;

    try {
      const requestData = {
        file_id: fileId.value,
        user_password: userPassword.value,
        owner_password: ownerPassword.value || userPassword.value,
        allow_printing: allowPrinting.value,
        allow_copying: allowCopying.value,
        preview_only: true // Add a flag to indicate this is just a preview
      };

      const headers = {
        'Content-Type': 'application/json'
      };

      // Add API key if user is authenticated
      if (authStore.token) {
        headers['X-API-Key'] = authStore.user?.apiKey;
      }

      const response = await axios.post(
          `/python-api/protect`,
          requestData,
          { headers }
      );

      // Get the preview PDF
      if (response.data && response.data.id) {
        const previewResponse = await axios.get(
            `/python-api/download/${response.data.id}`,
            { responseType: 'blob' }
        );

        // If we had a previous preview, revoke its URL
        if (previewPdfUrl.value) {
          URL.revokeObjectURL(previewPdfUrl.value);
        }

        // Create a new object URL for the preview
        previewPdfUrl.value = URL.createObjectURL(new Blob([previewResponse.data]));
        isPreviewProtected.value = true;
      }
    } catch (err) {
      console.error('Error creating protection preview:', err);
      // If preview fails, just use the original PDF
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewProtected.value = false;
      }
    } finally {
      previewPending.value = false;
    }
  }, 500); // 500ms debounce
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

        `/python-api/protect`,

        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;

    resultFileId.value = response.data.id;
    operationSuccess.value = true;
    resultFilename.value = response.data.filename || 'protected.pdf';
    showResultDialog.value = true;

    // Update the preview to show the final protected PDF
    const finalPdfResponse = await axios.get(
        `/python-api/download/${response.data.id}`,
        { responseType: 'blob' }
    );

    // If we had a previous preview, revoke its URL
    if (previewPdfUrl.value) {
      URL.revokeObjectURL(previewPdfUrl.value);
    }

    // Create a new object URL for the final protected PDF
    previewPdfUrl.value = URL.createObjectURL(new Blob([finalPdfResponse.data]));
    isPreviewProtected.value = true;

    // Update fileId to point to the new protected PDF
    fileId.value = response.data.id;
    pdfInfo.value = response.data;


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

        `/python-api/download/${resultFileUrl.value}`,

        { responseType: 'blob' }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', resultFilename.value);
    document.body.appendChild(link);
    link.click();
    link.remove();


    // Clean up the URL
    URL.revokeObjectURL(url);

  } catch (error) {
    console.error('Error downloading file:', error);
    error.value = t('pdf.downloadError');
  }
};


// Clean up object URLs when component is destroyed
onBeforeUnmount(() => {
  if (pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value);
  }
  if (previewPdfUrl.value) {
    URL.revokeObjectURL(previewPdfUrl.value);
  }
});

</script>