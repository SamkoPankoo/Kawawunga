<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.compressPdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.compressPdfDesc') }}</p>

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
            <v-chip v-if="isPreviewCompressed" color="success" size="small" class="ml-2">
              {{ $t('pdf.previewCompressed') }}
            </v-chip>
          </v-card-title>
          <v-card-text>
            <VuePdfEmbed
                v-if="currentPreviewUrl"
                :source="currentPreviewUrl"
                :page="currentPage"
                @loaded="numPages = $event.numPages"
                @rendered="pageLoaded"
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
          <v-card-title>{{ $t('pdf.compressionOptions') }}</v-card-title>
          <v-card-text>

            <v-radio-group
                v-model="compressionLevel"
                :label="$t('pdf.compressionLevel')"
                @update:model-value="previewCompression"

            >
              <v-radio
                  :label="$t('pdf.low')"
                  value="low"

              ></v-radio>
              <v-radio
                  :label="$t('pdf.medium')"
                  value="medium"
              ></v-radio>
              <v-radio
                  :label="$t('pdf.high')"
                  value="high"
              ></v-radio>

            </v-radio-group>

            <v-alert
                type="info"
                variant="tonal"
                class="mt-4"
                icon="mdi-information"
            >
              {{ $t('pdf.compressionNote') }}

            </v-alert>

            <v-alert
                v-if="originalFileSize && compressedFileSize"
                :type="compressionSuccess ? 'success' : 'warning'"
                variant="tonal"
                class="mt-4"
            >
              <p v-if="compressionSuccess">
                {{ $t('pdf.compressionResult', {
                from: formatFileSize(originalFileSize),
                to: formatFileSize(compressedFileSize),
                percent: Math.round((1 - compressedFileSize / originalFileSize) * 100)
              }) }}
              </p>
              <p v-else>
                {{ $t('pdf.noCompressionResult') }}
              </p>

            </v-alert>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canCompress || processing"
                :loading="processing"
                @click="compressPdf"

                prepend-icon="mdi-file-compare"

                size="large"
            >
              {{ $t('pdf.applyCompression') }}
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
          <p>{{ $t('pdf.compressionApplied') }}</p>
          <p class="text-grey">{{ resultFilename }}</p>

          <p v-if="originalFileSize && finalCompressedSize">
            {{ $t('pdf.finalCompressionResult', {
            from: formatFileSize(originalFileSize),
            to: formatFileSize(finalCompressedSize),
            percent: Math.round((1 - finalCompressedSize / originalFileSize) * 100)
          }) }}
          </p>

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

import { ref, computed, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import VuePdfEmbed from 'vue-pdf-embed';
import {useAuthStore} from '@/stores/auth';
import LogOperation from "@/components/pdf/LogOperation.vue";


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
const isPreviewCompressed = ref(false);
const previewPending = ref(false);
const previewTimeout = ref(null);

// Current preview that's being displayed
const currentPreviewUrl = computed(() => {
  return previewPdfUrl.value || pdfUrl.value;
});


// Compression options
const compressionLevel = ref('medium');
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);


// File size tracking for compression metrics
const originalFileSize = ref(null);
const compressedFileSize = ref(null);
const finalCompressedSize = ref(null);
const compressionSuccess = computed(() => {
  if (!originalFileSize.value || !compressedFileSize.value) return false;
  return compressedFileSize.value < originalFileSize.value;
});


const rules = {
  required: value => !!value || t('validation.required')
};

const canCompress = computed(() => {

  return pdfInfo.value && compressionLevel.value;
});

const getLogDescription = () => {
  if (originalFileSize.value && finalCompressedSize.value) {
    const compressionPercent = Math.round((1 - finalCompressedSize.value / originalFileSize.value) * 100);
    return `Compressed PDF by ${compressionPercent}% (${compressionLevel.value} level)`;
  }
  return `Compressed PDF (${compressionLevel.value} level)`;
};

const getLogMetadata = () => {
  return {
    fileName: selectedFile.value?.name,
    compressionLevel: compressionLevel.value,
    originalSize: originalFileSize.value,
    compressedSize: finalCompressedSize.value,
    compressionRatio: originalFileSize.value ? (1 - finalCompressedSize.value / originalFileSize.value) : null,
    resultFile: resultFilename.value,
    timestamp: new Date().toISOString()
  };

};

const handleFileChange = () => {
  if (selectedFile.value) {
    pdfUrl.value = URL.createObjectURL(selectedFile.value);

    // Save original file size
    originalFileSize.value = selectedFile.value.size;
    // Reset preview when changing file
    previewPdfUrl.value = null;
    compressedFileSize.value = null;
    isPreviewCompressed.value = false;
    uploadFile();
  } else {
    pdfUrl.value = null;
    previewPdfUrl.value = null;
    pdfInfo.value = null;
    fileId.value = null;
    originalFileSize.value = null;
    compressedFileSize.value = null;
    isPreviewCompressed.value = false;

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


const formatFileSize = (bytes) => {
  if (!bytes) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
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


    // Create initial preview with default compression level
    previewCompression();

  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};


// Function to create live preview of compression
const previewCompression = () => {
  // Debounce preview requests
  if (previewTimeout.value) {
    clearTimeout(previewTimeout.value);
  }

  previewTimeout.value = setTimeout(async () => {
    if (!fileId.value || previewPending.value) return;

    // Only preview if we have valid compression settings
    if (!canCompress.value) {
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewCompressed.value = false;
      }
      return;
    }

    previewPending.value = true;

    try {
      const requestData = {
        file_id: fileId.value,
        compression_level: compressionLevel.value,
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
          `/python-api/compress`,
          requestData,
          { headers }
      );

      // Get the preview PDF
      if (response.data && response.data.id) {
        const previewResponse = await axios.get(
            `/python-api/download/${response.data.id}`,
            { responseType: 'blob' }
        );

        // Record compressed file size for comparison
        compressedFileSize.value = previewResponse.data.size;

        // If we had a previous preview, revoke its URL
        if (previewPdfUrl.value) {
          URL.revokeObjectURL(previewPdfUrl.value);
        }

        // Create a new object URL for the preview
        previewPdfUrl.value = URL.createObjectURL(new Blob([previewResponse.data]));
        isPreviewCompressed.value = true;
      }
    } catch (err) {
      console.error('Error creating compression preview:', err);
      // If preview fails, just use the original PDF
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewCompressed.value = false;
      }
    } finally {
      previewPending.value = false;
    }
  }, 500); // 500ms debounce
};


const compressPdf = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    const requestData = {
      file_id: fileId.value,
      compression_level: compressionLevel.value
    };

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(

        `/python-api/compress`,

        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;

    resultFileId.value = response.data.id;
    operationSuccess.value = true;
    resultFilename.value = response.data.filename || 'compressed.pdf';

    // Get final PDF to measure size
    const finalPdfResponse = await axios.get(
        `/python-api/download/${response.data.id}`,
        { responseType: 'blob' }
    );

    // Set final compressed size for results dialog
    finalCompressedSize.value = finalPdfResponse.data.size;

    // Show results dialog
    showResultDialog.value = true;

    // Update the preview to show the final compressed PDF
    // If we had a previous preview, revoke its URL
    if (previewPdfUrl.value) {
      URL.revokeObjectURL(previewPdfUrl.value);
    }

    // Create a new object URL for the final compressed PDF
    previewPdfUrl.value = URL.createObjectURL(new Blob([finalPdfResponse.data]));
    isPreviewCompressed.value = true;

    // Update fileId to point to the new compressed PDF
    fileId.value = response.data.id;
    pdfInfo.value = response.data;


  } catch (error) {
    console.error('Error compressing PDF:', error);
    error.value = error.response?.data?.error || t('pdf.compressError');
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