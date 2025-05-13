<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.editMetadata') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.editMetadataDesc') }}</p>

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
          <v-card-title>{{ $t('pdf.metadataOptions') }}</v-card-title>
          <v-card-text>
            <v-text-field
                v-model="metadata.title"
                :label="$t('pdf.title')"
                class="mb-2"
                clearable
            ></v-text-field>

            <v-text-field
                v-model="metadata.author"
                :label="$t('pdf.author')"
                class="mb-2"
                clearable
            ></v-text-field>

            <v-text-field
                v-model="metadata.subject"
                :label="$t('pdf.subject')"
                class="mb-2"
                clearable
            ></v-text-field>

            <v-text-field
                v-model="metadata.keywords"
                :label="$t('pdf.keywords')"
                :hint="$t('pdf.keywordsHint')"
                persistent-hint
                class="mb-4"
                clearable
            ></v-text-field>

            <v-alert
                type="info"
                variant="tonal"
                class="mt-4"
                icon="mdi-information"
            >
              {{ $t('pdf.metadataNote') }}
            </v-alert>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canUpdateMetadata || processing"
                :loading="processing"
                @click="updateMetadata"
                prepend-icon="mdi-file-document-edit"
                size="large"
            >
              {{ $t('pdf.applyMetadata') }}
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
          <p>{{ $t('pdf.metadataApplied') }}</p>
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

// Metadata options
const metadata = ref({
  title: '',
  author: '',
  subject: '',
  keywords: ''
});
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);

const rules = {
  required: value => !!value || t('validation.required')
};

const canUpdateMetadata = computed(() => {
  return pdfInfo.value &&
      (metadata.value.title ||
          metadata.value.author ||
          metadata.value.subject ||
          metadata.value.keywords);
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

    // Attempt to read existing metadata
    try {
      const metadataResponse = await axios.get(
          `${import.meta.env.VITE_PYTHON_API_URL}/metadata/${fileId.value}`
      );

      if (metadataResponse.data && metadataResponse.data.metadata) {
        metadata.value = {
          title: metadataResponse.data.metadata.title || '',
          author: metadataResponse.data.metadata.author || '',
          subject: metadataResponse.data.metadata.subject || '',
          keywords: metadataResponse.data.metadata.keywords || ''
        };
      }
    } catch (metadataError) {
      console.warn('Could not fetch existing metadata:', metadataError);
      // Not critical, continue without existing metadata
    }
  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};

const updateMetadata = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    const requestData = {
      file_id: fileId.value,
      metadata: {
        title: metadata.value.title,
        author: metadata.value.author,
        subject: metadata.value.subject,
        keywords: metadata.value.keywords
      }
    };

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/edit-metadata`,
        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;
    resultFilename.value = response.data.filename || 'metadata_updated.pdf';
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error updating metadata:', error);
    error.value = error.response?.data?.error || t('pdf.metadataError');
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