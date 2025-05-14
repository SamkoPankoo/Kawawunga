<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.pdfToImage') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.pdfToImageDesc') }}</p>

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

            <VuePdfEmbed
                v-if="pdfUrl"
                :source="pdfUrl"

                :page="currentPage"
                @num-pages="numPages = $event"
                @page-loaded="pageLoaded"
                @error="handleError"
                style="display: block; width: 100%;"

            ></VuePdfEmbed>

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
          <v-card-title>{{ $t('pdf.conversionOptions') }}</v-card-title>
          <v-card-text>
            <v-select
                v-model="outputFormat"
                :items="formatOptions"
                :label="$t('pdf.outputFormat')"
                class="mb-4"
            ></v-select>

            <v-slider
                v-model="dpi"
                :label="$t('pdf.quality')"
                min="72"
                max="600"
                :step="72"
                thumb-label
                class="mb-4"
            >
              <template v-slot:thumb-label>
                {{ dpi }} DPI
              </template>
            </v-slider>

            <v-divider class="my-4"></v-divider>

            <h3 class="text-subtitle-1 font-weight-bold mb-2">{{ $t('pdf.pageSelection') }}</h3>
            <v-select
                v-model="pageSelection"
                :items="pageSelectionOptions"
                @update:model-value="updatePageRange"
            ></v-select>

            <template v-if="pageSelection === 'range'">
              <v-row>
                <v-col cols="6">
                  <v-text-field
                      v-model="pageRange.from"
                      type="number"
                      :label="$t('pdf.from')"
                      min="1"
                      :max="numPages"
                      :rules="[rules.required, rules.validPage]"
                  ></v-text-field>
                </v-col>
                <v-col cols="6">
                  <v-text-field
                      v-model="pageRange.to"
                      type="number"
                      :label="$t('pdf.to')"
                      min="1"
                      :max="numPages"
                      :rules="[rules.required, rules.validPage, validateRange]"
                  ></v-text-field>
                </v-col>
              </v-row>
            </template>

            <template v-if="pageSelection === 'custom'">
              <v-text-field
                  v-model="customPages"
                  :label="$t('pdf.customPages')"
                  :hint="$t('pdf.customPagesHint')"
                  persistent-hint
                  :rules="[rules.required, validateCustomPages]"
              ></v-text-field>
            </template>

            <v-switch
                v-model="createZipFile"
                :label="$t('pdf.createZipFile')"
                class="mt-4"
                :disabled="numPages <= 1"
            ></v-switch>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canConvert || processing"
                :loading="processing"
                @click="convertToImages"
                prepend-icon="mdi-file-image"
                size="large"
            >
              {{ $t('pdf.convert') }}
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
          <p>{{ $t('pdf.conversionComplete') }}</p>
          <v-chip class="my-2" color="primary">{{ resultFiles.length }} {{ $t('pdf.imagesCreated') }}</v-chip>

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
                          :src="`${apiBaseUrl}/download/${file.id}`"
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

    <LogOperation
        v-if="operationSuccess"
        :operation="'compress'"
        :description="getLogDescription()"
        :metadata="getLogMetadata()"

    />

  </v-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

import VuePdfEmbed from "vue-pdf-embed";
import {useAuthStore} from '@/stores/auth';
import LogOperation from '@/components/pdf/LogOperation.vue';
const operationSuccess = ref(false);
const resultFileId = ref(null);


const apiBaseUrl = import.meta.env.VITE_PYTHON_API_URL;

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

// Conversion options
const outputFormat = ref('png');
const dpi = ref(300);
const pageSelection = ref('all');
const pageRange = ref({ from: 1, to: 1 });
const customPages = ref('');
const createZipFile = ref(true);
const processing = ref(false);
const showResultDialog = ref(false);
const resultFiles = ref([]);
const zipId = ref(null);

const formatOptions = [
  { title: 'PNG', value: 'png' },
  { title: 'JPEG', value: 'jpg' }
];

const pageSelectionOptions = computed(() => [
  { title: t('pdf.allPages'), value: 'all' },
  { title: t('pdf.currentPage'), value: 'current' },
  { title: t('pdf.pageRange'), value: 'range' },
  { title: t('pdf.customPages'), value: 'custom' }
]);

const rules = {
  required: value => !!value || t('validation.required'),
  validPage: value => {
    const page = parseInt(value);
    return (page >= 1 && page <= numPages.value) || t('validation.pageRange', { max: numPages.value });
  }
};

const validateRange = () => {
  const start = parseInt(pageRange.value.from);
  const end = parseInt(pageRange.value.to);
  return start <= end || t('validation.startEndOrder');
};

const validateCustomPages = (value) => {
  if (!value) return true;

  // Check format (comma-separated numbers)
  const pagePattern = /^(\d+)(,\s*\d+)*$/;
  if (!pagePattern.test(value)) {
    return t('validation.extractPagesFormat');
  }

  // Check if all page numbers are valid
  const pages = value.split(',').map(p => parseInt(p.trim()));
  const invalidPages = pages.filter(p => p < 1 || p > numPages.value);

  if (invalidPages.length > 0) {
    return t('validation.invalidPages', { pages: invalidPages.join(', '), max: numPages.value });
  }

  return true;
};

const canConvert = computed(() => {
  if (!pdfInfo.value) return false;

  if (pageSelection.value === 'range') {
    const start = parseInt(pageRange.value.from);
    const end = parseInt(pageRange.value.to);
    return !isNaN(start) && !isNaN(end) && start >= 1 && end <= numPages.value && start <= end;
  }

  if (pageSelection.value === 'custom') {
    return validateCustomPages(customPages.value) === true;
  }

  return true;
});

watch(numPages, (newValue) => {
  if (newValue > 0) {
    pageRange.value.to = newValue;
  }
});


const getLogDescription = () => {
  let pagesDesc = '';
  if (pageSelection.value === 'all') {
    pagesDesc = `all ${numPages.value} pages`;
  } else if (pageSelection.value === 'current') {
    pagesDesc = `page ${currentPage.value}`;
  } else if (pageSelection.value === 'range') {
    pagesDesc = `pages ${pageRange.value.from} to ${pageRange.value.to}`;
  } else if (pageSelection.value === 'custom') {
    pagesDesc = `selected pages (${customPages.value})`;
  }

  return `Converted ${pagesDesc} to ${outputFormat.value.toUpperCase()} images (${dpi.value} DPI)`;
};

const getLogMetadata = () => {
  return {
    fileName: selectedFile.value?.name,
    format: outputFormat.value,
    dpi: dpi.value,
    pageSelection: pageSelection.value,
    resultFiles: resultFiles.value.length,
    zipFile: !!zipId.value,
    timestamp: new Date().toISOString()
  };
};



watch(currentPage, () => {
  if (pageSelection.value === 'current') {
    pageRange.value = { from: currentPage.value, to: currentPage.value };
  }
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

const updatePageRange = () => {
  if (pageSelection.value === 'all') {
    pageRange.value = { from: 1, to: numPages.value };
  } else if (pageSelection.value === 'current') {
    pageRange.value = { from: currentPage.value, to: currentPage.value };
  } else if (pageSelection.value === 'range') {
    pageRange.value = { from: 1, to: numPages.value };
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
        `${apiBaseUrl}/upload`,
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

const convertToImages = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    let pages = [];

    if (pageSelection.value === 'all') {
      // All pages will be handled by the server
    } else if (pageSelection.value === 'current') {
      pages = [currentPage.value];
    } else if (pageSelection.value === 'range') {
      const start = parseInt(pageRange.value.from);
      const end = parseInt(pageRange.value.to);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
    } else if (pageSelection.value === 'custom') {
      pages = customPages.value.split(',').map(p => parseInt(p.trim()));
    }

    const requestData = {
      file_id: fileId.value,
      format: outputFormat.value,
      dpi: dpi.value,
      pages: pages.length > 0 ? pages : null,
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
        `${apiBaseUrl}/pdf-to-image`,
        requestData,
        { headers }
    );

    resultFiles.value = response.data.files || [];

    if (resultFiles.value.length > 0) {
      resultFileId.value = resultFiles.value[0].id;
      operationSuccess.value = true;
    }


    // Check if there's a ZIP file
    if (resultFiles.value.length > 0 && resultFiles.value[0].zip_id) {
      zipId.value = resultFiles.value[0].zip_id;
    } else {
      zipId.value = null;
    }

    showResultDialog.value = true;
  } catch (error) {
    console.error('Error converting PDF to images:', error);
    error.value = error.response?.data?.error || t('pdf.conversionError');
  } finally {
    processing.value = false;
  }
};

const downloadResult = async () => {
  try {
    // If we have a ZIP file, download it
    if (zipId.value) {

      console.log("Attempting to download ZIP file with ID:", zipId.value);

      // Create URLs for each file in the result set
      const fileUrls = resultFiles.value.map(file => ({
        id: file.id,
        name: file.filename,
        url: `${apiBaseUrl}/download/${file.id}`
      }));

      console.log("Available files:", fileUrls);

      try {
        // Try to download ZIP first
        const response = await axios.get(
            `${apiBaseUrl}/download-zip/${zipId.value}`,
            {
              responseType: 'blob',
              headers: {
                'Accept': 'application/zip, application/json'
              }
            }
        );

        console.log("ZIP response received:", response.status);

        // Create download link
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'pdf_images.zip');
        document.body.appendChild(link);
        link.click();
        link.remove();

      } catch (err) {
        console.error("ZIP download failed, details:", err);

        // Check if we need to try an alternative URL
        try {
          console.log("Trying alternative ZIP format");

          // Try adding .zip extension explicitly
          const altResponse = await axios.get(
              `${apiBaseUrl}/download/${zipId.value}.zip`,
              {
                responseType: 'blob'
              }
          );

          const url = window.URL.createObjectURL(new Blob([altResponse.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', 'pdf_images.zip');
          document.body.appendChild(link);
          link.click();
          link.remove();
          return;
        } catch (altErr) {
          console.error("Alternative ZIP download also failed");

          // Fall back to downloading all files individually
          if (confirm("ZIP download failed. Would you like to download the first image instead?")) {
            downloadFirstImage();
          }
        }
      }
    } else {
      downloadFirstImage();
    }
  } catch (error) {
    console.error('Error in download function:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
    }
    error.value = t('pdf.downloadError');
  }
};

// Helper to download first image
const downloadFirstImage = async () => {
  if (resultFiles.value.length > 0) {
    const file = resultFiles.value[0];
    try {

      const response = await axios.get(
          `${apiBaseUrl}/download/${file.id}`,
          { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', file.filename);
      document.body.appendChild(link);
      link.click();
      link.remove();

    } catch (err) {
      console.error("Error downloading single image:", err);
      error.value = t('pdf.downloadError');
    }

  }
};

// Initialize
updatePageRange();
</script>