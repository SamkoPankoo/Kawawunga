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
          <v-card-title class="d-flex align-center">
            <span>{{ $t('pdf.preview') }}</span>
            <v-spacer></v-spacer>
            <v-chip v-if="isPreviewMetadataEdited" color="success" size="small" class="ml-2">
              {{ $t('pdf.previewMetadataEdited') }}
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
          <v-card-title>{{ $t('pdf.metadataOptions') }}</v-card-title>
          <v-card-text>
            <v-text-field
                v-model="metadata.title"
                :label="$t('pdf.title')"
                class="mb-2"
                clearable
                @update:model-value="previewMetadataChanges"
            ></v-text-field>

            <v-text-field
                v-model="metadata.author"
                :label="$t('pdf.author')"
                class="mb-2"
                clearable
                @update:model-value="previewMetadataChanges"
            ></v-text-field>

            <v-text-field
                v-model="metadata.subject"
                :label="$t('pdf.subject')"
                class="mb-2"
                clearable
                @update:model-value="previewMetadataChanges"
            ></v-text-field>

            <v-text-field
                v-model="metadata.keywords"
                :label="$t('pdf.keywords')"
                :hint="$t('pdf.keywordsHint')"
                persistent-hint
                class="mb-4"
                clearable
                @update:model-value="previewMetadataChanges"
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

import { ref, computed, onBeforeUnmount } from 'vue';
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
const isPreviewMetadataEdited = ref(false);
const previewPending = ref(false);
const previewTimeout = ref(null);

// Current preview that's being displayed
const currentPreviewUrl = computed(() => {
  return previewPdfUrl.value || pdfUrl.value;
});


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

    // Reset preview when changing file
    previewPdfUrl.value = null;
    isPreviewMetadataEdited.value = false;
    uploadFile();
  } else {
    pdfUrl.value = null;
    previewPdfUrl.value = null;
    pdfInfo.value = null;
    fileId.value = null;
    isPreviewMetadataEdited.value = false;

  }
};

const pageLoaded = () => {
  loading.value = false;
};

const handleError = (err) => {
  console.error('PDF error:', err);
  loading.value = false;
};



const getLogDescription = () => {
  const fields = [];
  if (metadata.value.title) fields.push('title');
  if (metadata.value.author) fields.push('author');
  if (metadata.value.subject) fields.push('subject');
  if (metadata.value.keywords) fields.push('keywords');

  return `Updated PDF metadata (${fields.join(', ')})`;
};

const getLogMetadata = () => {
  return {
    fileName: selectedFile.value?.name,
    metadataFields: metadata.value,
    resultFile: resultFilename.value,
    timestamp: new Date().toISOString()
  };
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

    // Attempt to read existing metadata
    try {
      const metadataResponse = await axios.get(

          `/python-api/metadata/${fileId.value}`

      );

      if (metadataResponse.data && metadataResponse.data.metadata) {
        metadata.value = {
          title: metadataResponse.data.metadata.title || '',
          author: metadataResponse.data.metadata.author || '',
          subject: metadataResponse.data.metadata.subject || '',
          keywords: metadataResponse.data.metadata.keywords || ''
        };


        // Create initial preview with existing metadata
        if (canUpdateMetadata.value) {
          previewMetadataChanges();
        }

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


// Function to create live preview of metadata changes
const previewMetadataChanges = () => {
  // Debounce preview requests
  if (previewTimeout.value) {
    clearTimeout(previewTimeout.value);
  }

  previewTimeout.value = setTimeout(async () => {
    if (!fileId.value || previewPending.value) return;

    // Only preview if we have valid metadata
    if (!canUpdateMetadata.value) {
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewMetadataEdited.value = false;
      }
      return;
    }

    previewPending.value = true;

    try {
      const requestData = {
        file_id: fileId.value,
        metadata: {
          title: metadata.value.title,
          author: metadata.value.author,
          subject: metadata.value.subject,
          keywords: metadata.value.keywords
        },
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
          `/python-api/edit-metadata`,
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
        isPreviewMetadataEdited.value = true;
      }
    } catch (err) {
      console.error('Error creating metadata preview:', err);
      // If preview fails, just use the original PDF
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewMetadataEdited.value = false;
      }
    } finally {
      previewPending.value = false;
    }
  }, 500); // 500ms debounce
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

        `/python-api/edit-metadata`,

        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;


    resultFileId.value = response.data.id;
    operationSuccess.value = true;
    resultFilename.value = response.data.filename || 'metadata_updated.pdf';
    showResultDialog.value = true;

    // Update the preview to show the final PDF with updated metadata
    const finalPdfResponse = await axios.get(
        `/python-api/download/${response.data.id}`,
        { responseType: 'blob' }
    );

    // If we had a previous preview, revoke its URL
    if (previewPdfUrl.value) {
      URL.revokeObjectURL(previewPdfUrl.value);
    }

    // Create a new object URL for the final PDF
    previewPdfUrl.value = URL.createObjectURL(new Blob([finalPdfResponse.data]));
    isPreviewMetadataEdited.value = true;

    // Update fileId to point to the new PDF with updated metadata
    fileId.value = response.data.id;
    pdfInfo.value = response.data;

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