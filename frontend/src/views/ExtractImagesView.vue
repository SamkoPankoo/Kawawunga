<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.extractImages') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.extractImagesDesc') }}</p>

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
          <v-card-title>{{ $t('pdf.extractOptions') }}</v-card-title>
          <v-card-text>
            <v-switch
                v-model="createZipFile"
                :label="$t('pdf.createZipFile')"
                class="mb-4"
            ></v-switch>

            <v-alert
                type="info"
                variant="tonal"
                class="mt-4"
                icon="mdi-information"
            >
              {{ $t('pdf.extractImagesInfo') }}
            </v-alert>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!pdfInfo || processing"
                :loading="processing"
                @click="extractImages"
                prepend-icon="mdi-image-multiple"
                size="large"
            >
              {{ $t('pdf.extractImages') }}
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
          <p>{{ $t('pdf.imagesExtracted', { count: resultFiles.length }) }}</p>

          <v-chip class="my-2" color="primary">{{ resultFiles.length }} {{ $t('pdf.imagesFound') }}</v-chip>

          <v-expansion-panels v-if="resultFiles.length > 0" variant="accordion" class="mt-3">
            <v-expansion-panel title="Preview images">
              <template v-slot:text>
                <v-row>
                  <v-col
                      v-for="(file, index) in resultFiles.slice(0, 4)"
                      :key="index"
                      cols="6"
                      class="pa-2"
                  >
                    <v-card elevation="0" class="pa-2" variant="outlined">
                      <v-img
                          :src="`${import.meta.env.VITE_PYTHON_API_URL}/download/${file.id}`"
                          :alt="file.filename"
                          height="120"
                          cover
                          class="rounded"
                      ></v-img>
                      <div class="text-caption mt-1 text-truncate">{{ file.filename }}</div>
                    </v-card>
                  </v-col>
                </v-row>
                <v-alert
                    v-if="resultFiles.length > 4"
                    type="info"
                    density="compact"
                    class="mt-2"
                    variant="tonal"
                >
                  {{ $t('pdf.moreImagesAvailable', { count: resultFiles.length - 4 }) }}
                </v-alert>
              </template>
            </v-expansion-panel>
          </v-expansion-panels>
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
import { ref, computed } from 'vue';
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

// Extract options
const createZipFile = ref(true);
const processing = ref(false);
const showResultDialog = ref(false);
const resultFiles = ref([]);
const zipId = ref(null);

const rules = {
  required: value => !!value || t('validation.required')
};

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

const extractImages = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    const requestData = {
      file_id: fileId.value,
      create_zip: createZipFile.value
    };

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/extract-images`,
        requestData,
        { headers }
    );

    resultFiles.value = response.data.files || [];

    // Check if there's a ZIP file
    if (resultFiles.value.length > 0 && resultFiles.value[0].zip_id) {
      zipId.value = resultFiles.value[0].zip_id;
    } else {
      zipId.value = null;
    }

    showResultDialog.value = true;
  } catch (error) {
    console.error('Error extracting images:', error);
    error.value = error.response?.data?.error || t('pdf.extractImagesError');
  } finally {
    processing.value = false;
  }
};

const downloadResult = async () => {
  try {
    // If we have a ZIP file, download it
    if (zipId.value) {
      const response = await axios.get(
          `${import.meta.env.VITE_PYTHON_API_URL}/download-zip/${zipId.value}`,
          { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'extracted_images.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
    // Otherwise download the first image (or the only one)
    else if (resultFiles.value.length > 0) {
      const file = resultFiles.value[0];
      const response = await axios.get(
          `${import.meta.env.VITE_PYTHON_API_URL}/download/${file.id}`,
          { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
  } catch (error) {
    console.error('Error downloading file:', error);
    error.value = t('pdf.downloadError');
  }
};
</script>