<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.watermarkPdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.watermarkPdfDesc') }}</p>

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
            <v-chip v-if="isPreviewWatermarked" color="success" size="small" class="ml-2">
              {{ $t('pdf.previewWatermarked') }}
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
          <v-card-title>{{ $t('pdf.watermarkOptions') }}</v-card-title>
          <v-card-text>
            <v-text-field
                v-model="watermarkText"
                :label="$t('pdf.watermarkText')"
                :rules="[rules.required]"
                class="mb-2"
                @update:model-value="updateWatermarkPreview"
            ></v-text-field>

            <v-slider
                v-model="watermarkOpacity"
                :label="$t('pdf.watermarkOpacity')"
                min="0"
                max="100"
                step="5"
                thumb-label
                class="mb-4"
                @update:model-value="updateWatermarkPreview"
            ></v-slider>

            <v-radio-group
                v-model="watermarkAngle"
                :label="$t('pdf.watermarkAngle')"
                inline
                @update:model-value="updateWatermarkPreview"
            >
              <v-radio
                  :label="$t('pdf.horizontal')"
                  value="0"
              ></v-radio>
              <v-radio
                  :label="$t('pdf.diagonal')"
                  value="45"
              ></v-radio>
              <v-radio
                  :label="$t('pdf.vertical')"
                  value="90"
              ></v-radio>
            </v-radio-group>

            <v-select
                v-model="watermarkColor"
                :items="colorOptions"
                :label="$t('pdf.watermarkColor')"
                item-title="text"
                item-value="value"
                return-object
                class="mb-4"
                @update:model-value="updateWatermarkPreview"
            >
              <template v-slot:selection="{ item }">
                <div class="d-flex align-center">
                  <v-avatar
                      size="24"
                      :color="item.raw.value"
                      class="mr-2"
                  ></v-avatar>
                  {{ item.raw.text }}
                </div>
              </template>
              <template v-slot:item="{ item, props }">
                <v-list-item v-bind="props">
                  <template v-slot:prepend>
                    <v-avatar
                        size="24"
                        :color="item.value"
                    ></v-avatar>
                  </template>
                  <v-list-item-title>{{ item.title }}</v-list-item-title>
                </v-list-item>
              </template>
            </v-select>

            <v-select
                v-model="watermarkSize"
                :items="sizeOptions"
                :label="$t('pdf.watermarkSize')"
                class="mb-4"
                @update:model-value="updateWatermarkPreview"
            ></v-select>

            <v-divider class="my-4"></v-divider>

            <v-select
                v-model="pageSelection"
                :items="pageSelectionOptions"
                :label="$t('pdf.pageSelection')"
                @update:model-value="updatePageRangeAndPreview"
            ></v-select>

            <v-row v-if="pageSelection === 'range'">
              <v-col cols="6">
                <v-text-field
                    v-model="pageRange.from"
                    type="number"
                    :label="$t('pdf.from')"
                    min="1"
                    :max="numPages"
                    :rules="[rules.required, rules.validPage]"
                    @update:model-value="updateWatermarkPreview"
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
                    @update:model-value="updateWatermarkPreview"
                ></v-text-field>
              </v-col>
            </v-row>

            <v-row v-if="pageSelection === 'custom'">
              <v-col cols="12">
                <v-text-field
                    v-model="customPages"
                    :label="$t('pdf.customPages')"
                    :hint="$t('pdf.customPagesHint')"
                    persistent-hint
                    :rules="[rules.required, validateCustomPages]"
                    @update:model-value="updateWatermarkPreview"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canApplyWatermark || processing"
                :loading="processing"
                @click="applyWatermark"
                prepend-icon="mdi-water"
                size="large"
            >
              {{ $t('pdf.applyWatermark') }}
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
          <p>{{ $t('pdf.watermarkApplied') }}</p>
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
        :operation="'watermark'"
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

const { t } = useI18n();

const selectedFile = ref(null);
const pdfUrl = ref(null);
const pdfInfo = ref(null);
const currentPage = ref(1);
const numPages = ref(0);
const loading = ref(false);
const error = ref(null);
const fileId = ref(null);

import LogOperation from '@/components/pdf/LogOperation.vue';
const operationSuccess = ref(false);
const resultFileId = ref(null);

// For live preview
const previewPdfUrl = ref(null);
const isPreviewWatermarked = ref(false);
const previewPending = ref(false);
const previewTimeout = ref(null);

// Current preview that's being displayed
const currentPreviewUrl = computed(() => {
  return previewPdfUrl.value || pdfUrl.value;
});

// Watermark options
const watermarkText = ref('CONFIDENTIAL');
const watermarkOpacity = ref(30);
const watermarkAngle = ref('45');
const watermarkColor = ref({ text: 'Gray', value: 'gray' });
const watermarkSize = ref(48);
const pageSelection = ref('all');
const pageRange = ref({ from: 1, to: 1 });
const customPages = ref('');
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);

const colorOptions = [
  { text: 'Gray', value: 'gray' },
  { text: 'Red', value: 'red' },
  { text: 'Blue', value: 'blue' },
  { text: 'Green', value: 'green' },
  { text: 'Black', value: 'black' }
];

const sizeOptions = [
  { title: 'Small (24px)', value: 24 },
  { title: 'Medium (36px)', value: 36 },
  { title: 'Large (48px)', value: 48 },
  { title: 'Extra Large (72px)', value: 72 }
];

const pageSelectionOptions = computed(() => [
  { title: t('pdf.allPages'), value: 'all' },
  { title: t('pdf.currentPage'), value: 'current' },
  { title: t('pdf.pageRange'), value: 'range' },
  { title: t('pdf.customPages'), value: 'custom' }
]);

const getLogDescription = () => {
  let pageDesc = '';
  if (pageSelection.value === 'all') {
    pageDesc = `all ${numPages.value} pages`;
  } else if (pageSelection.value === 'current') {
    pageDesc = `page ${currentPage.value}`;
  } else if (pageSelection.value === 'range') {
    pageDesc = `pages ${pageRange.value.from} to ${pageRange.value.to}`;
  } else if (pageSelection.value === 'custom') {
    pageDesc = `pages ${customPages.value}`;
  }
  return `Added "${watermarkText.value}" watermark to ${pageDesc}`;
};

const getLogMetadata = () => {
  return {
    fileName: selectedFile.value?.name,
    watermarkText: watermarkText.value,
    watermarkOptions: {
      opacity: watermarkOpacity.value,
      color: watermarkColor.value?.value,
      size: watermarkSize.value,
      angle: watermarkAngle.value
    },
    pageSelection: pageSelection.value,
    resultFile: resultFilename.value,
    timestamp: new Date().toISOString()
  };
};

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

const canApplyWatermark = computed(() => {
  if (!pdfInfo.value || !watermarkText.value) return false;

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

watch(currentPage, () => {
  if (pageSelection.value === 'current') {
    pageRange.value = { from: currentPage.value, to: currentPage.value };
    updateWatermarkPreview();
  }
});

const handleFileChange = () => {
  if (selectedFile.value) {
    pdfUrl.value = URL.createObjectURL(selectedFile.value);
    // Reset preview when changing file
    previewPdfUrl.value = null;
    isPreviewWatermarked.value = false;
    uploadFile();
  } else {
    pdfUrl.value = null;
    previewPdfUrl.value = null;
    pdfInfo.value = null;
    fileId.value = null;
    isPreviewWatermarked.value = false;
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

const updatePageRangeAndPreview = () => {
  updatePageRange();
  updateWatermarkPreview();
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

    // Create initial watermark preview
    updateWatermarkPreview();
  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};

// Function to create live preview of watermark
const updateWatermarkPreview = () => {
  // Debounce preview requests
  if (previewTimeout.value) {
    clearTimeout(previewTimeout.value);
  }

  previewTimeout.value = setTimeout(async () => {
    if (!fileId.value || previewPending.value) return;

    // Only preview if we have valid watermark settings
    if (!canApplyWatermark.value) {
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewWatermarked.value = false;
      }
      return;
    }

    previewPending.value = true;

    try {
      let pages = [];

      if (pageSelection.value === 'all') {
        pages = Array.from({ length: numPages.value }, (_, i) => i + 1);
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
        text: watermarkText.value,
        opacity: watermarkOpacity.value / 100,
        color: watermarkColor.value.value,
        size: watermarkSize.value,
        angle: parseInt(watermarkAngle.value),
        pages: pages,
        preview_only: true // Add a flag to indicate this is just a preview
      };

      const response = await axios.post(
          `/python-api/watermark`,
          requestData
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
        isPreviewWatermarked.value = true;
      }
    } catch (err) {
      console.error('Error creating watermark preview:', err);
      // If preview fails, just use the original PDF
      if (previewPdfUrl.value) {
        URL.revokeObjectURL(previewPdfUrl.value);
        previewPdfUrl.value = null;
        isPreviewWatermarked.value = false;
      }
    } finally {
      previewPending.value = false;
    }
  }, 500); // 500ms debounce
};

const applyWatermark = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    let pages = [];

    if (pageSelection.value === 'all') {
      pages = Array.from({ length: numPages.value }, (_, i) => i + 1);
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
      text: watermarkText.value,
      opacity: watermarkOpacity.value / 100,
      color: watermarkColor.value.value,
      size: watermarkSize.value,
      angle: parseInt(watermarkAngle.value),
      pages: pages
    };

    const response = await axios.post(
        `/python-api/watermark`,
        requestData
    );

    resultFileUrl.value = response.data.id;
    resultFileId.value = response.data.id;
    operationSuccess.value = true;
    resultFilename.value = response.data.filename || 'watermarked.pdf';
    showResultDialog.value = true;

    // Update the preview to show the final watermarked PDF
    const finalPdfResponse = await axios.get(
        `/python-api/download/${response.data.id}`,
        { responseType: 'blob' }
    );

    // If we had a previous preview, revoke its URL
    if (previewPdfUrl.value) {
      URL.revokeObjectURL(previewPdfUrl.value);
    }

    // Create a new object URL for the final watermarked PDF
    previewPdfUrl.value = URL.createObjectURL(new Blob([finalPdfResponse.data]));
    isPreviewWatermarked.value = true;

    // Update fileId to point to the new watermarked PDF
    fileId.value = response.data.id;
    pdfInfo.value = response.data;

  } catch (error) {
    console.error('Error applying watermark:', error);
    error.value = error.response?.data?.error || t('pdf.watermarkError');
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

// Initialize
updatePageRange();
</script>