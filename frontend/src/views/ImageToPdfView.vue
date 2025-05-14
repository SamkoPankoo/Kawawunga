<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.imageToPdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.imageToPdfDesc') }}</p>

            <v-file-input
                v-model="selectedFiles"
                :label="$t('pdf.dropImagesHere')"
                accept="image/*"
                prepend-icon="mdi-image-multiple"
                :rules="[rules.required]"
                multiple
                chips
                counter
                show-size
                @update:model-value="handleFileSelection"
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

    <v-row v-if="selectedFiles.length > 0">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            {{ $t('pdf.selectedImages') }} ({{ selectedFiles.length }})
          </v-card-title>
          <v-card-text class="pa-0">
            <v-list>
              <div class="d-flex align-center px-4 py-2 bg-grey-lighten-4">
                <h3 class="text-subtitle-1">{{ $t('pdf.imageOrder') }}</h3>
                <v-spacer></v-spacer>
                <v-btn
                    color="primary"
                    size="small"
                    icon="mdi-arrow-up"
                    @click="reorderFiles('up')"
                    :disabled="!selectedFileIndex || selectedFileIndex === 0"
                    class="mr-1"
                ></v-btn>
                <v-btn
                    color="primary"
                    size="small"
                    icon="mdi-arrow-down"
                    @click="reorderFiles('down')"
                    :disabled="!selectedFileIndex || selectedFileIndex === selectedFiles.length - 1"
                ></v-btn>
              </div>
              <v-list-item
                  v-for="(file, index) in selectedFiles"
                  :key="index"
                  @click="selectedFileIndex = index"
                  :active="selectedFileIndex === index"
                  :title="file.name"
                  :subtitle="`${(file.size / 1024 / 1024).toFixed(2)} MB`"
                  lines="two"
              >
                <template v-slot:prepend>
                  <v-avatar size="48" class="mr-2">
                    <v-img
                        :src="getImagePreview(file)"
                        cover
                        :alt="file.name"
                    ></v-img>
                  </v-avatar>
                </template>
                <template v-slot:append>
                  <v-btn
                      icon="mdi-delete"
                      variant="text"
                      size="small"
                      color="error"
                      @click.stop="removeFile(index)"
                  ></v-btn>
                </template>
              </v-list-item>
            </v-list>
          </v-card-text>
          <v-divider></v-divider>

          <v-card-text>
            <h3 class="text-subtitle-1 font-weight-bold mb-2">{{ $t('pdf.pageSettings') }}</h3>
            <v-select
                v-model="pageSize"
                :items="pageSizeOptions"
                :label="$t('pdf.pageSize')"
                class="mb-2"
            ></v-select>
            <v-select
                v-model="pageOrientation"
                :items="pageOrientationOptions"
                :label="$t('pdf.pageOrientation')"
                class="mb-2"
            ></v-select>
            <v-alert
                type="info"
                variant="tonal"
                class="mt-4"
                icon="mdi-information"
            >
              {{ $t('pdf.imageToPdfNote') }}
            </v-alert>
          </v-card-text>

          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canConvert || processing"
                :loading="processing"
                @click="convertToPdf"
                prepend-icon="mdi-file-pdf-box"
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
        :operation="'imagetopdf'"
        :description="getLogDescription()"
        :metadata="getLogMetadata()"

    />
  </v-container>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';
import {useAuthStore} from '@/stores/auth';
import LogOperation from '@/components/pdf/LogOperation.vue';
const operationSuccess = ref(false);
const resultFileId = ref(null);
const { t } = useI18n();
const authStore = useAuthStore();

const selectedFiles = ref([]);
const selectedFileIndex = ref(null);
const error = ref(null);
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);
const imagePreviewUrls = ref({});

// Page settings
const pageSize = ref('A4');
const pageOrientation = ref('portrait');

const pageSizeOptions = [
  { title: 'A4', value: 'A4' },
  { title: 'A5', value: 'A5' },
  { title: 'Letter', value: 'Letter' },
  { title: 'Legal', value: 'Legal' }
];

const pageOrientationOptions = [
  { title: t('pdf.portrait'), value: 'portrait' },
  { title: t('pdf.landscape'), value: 'landscape' }
];

const rules = {
  required: value => !!value && value.length > 0 || t('validation.required')
};

const canConvert = computed(() => {
  return selectedFiles.value.length > 0;
});

const handleFileSelection = () => {
  if (selectedFiles.value.length > 0) {
    selectedFileIndex.value = 0;
    error.value = null;

    // Generate previews for new files
    selectedFiles.value.forEach(file => {
      if (!imagePreviewUrls.value[file.name]) {
        createImagePreview(file);
      }
    });
  } else {
    selectedFileIndex.value = null;
  }
};

const createImagePreview = (file) => {
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreviewUrls.value[file.name] = e.target.result;
  };
  reader.readAsDataURL(file);
};

const getImagePreview = (file) => {
  return imagePreviewUrls.value[file.name] || '';
};

const getLogDescription = () => {
  return `Converted ${selectedFiles.value.length} images to PDF`;
};

const getLogMetadata = () => {
  return {
    fileNames: selectedFiles.value.map(f => f.name),
    pageSize: pageSize.value,
    orientation: pageOrientation.value,
    fileCount: selectedFiles.value.length,
    resultFile: resultFilename.value,
    timestamp: new Date().toISOString()
  };
};
const removeFile = (index) => {
  const file = selectedFiles.value[index];

  // Remove from selectedFiles
  selectedFiles.value.splice(index, 1);

  // Update selectedFileIndex if necessary
  if (selectedFileIndex.value === index) {
    selectedFileIndex.value = selectedFiles.value.length > 0 ? 0 : null;
  } else if (selectedFileIndex.value > index) {
    selectedFileIndex.value--;
  }

  // Clean up preview URL
  if (file && imagePreviewUrls.value[file.name]) {
    URL.revokeObjectURL(imagePreviewUrls.value[file.name]);
    delete imagePreviewUrls.value[file.name];
  }
};

const reorderFiles = (direction) => {
  if (!selectedFileIndex.value && selectedFileIndex.value !== 0) return;

  const currentIndex = selectedFileIndex.value;
  const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;

  if (newIndex < 0 || newIndex >= selectedFiles.value.length) return;

  const temp = selectedFiles.value[currentIndex];
  selectedFiles.value[currentIndex] = selectedFiles.value[newIndex];
  selectedFiles.value[newIndex] = temp;

  selectedFileIndex.value = newIndex;
};

const convertToPdf = async () => {
  if (selectedFiles.value.length === 0) {
    error.value = t('pdf.noImagesSelected');
    return;
  }

  processing.value = true;
  error.value = null;

  try {
    const formData = new FormData();

    // Add each image file
    selectedFiles.value.forEach((file, index) => {
      formData.append(`image${index+1}`, file);
    });

    // Add configuration
    formData.append('page_size', pageSize.value);
    formData.append('orientation', pageOrientation.value);

    const headers = {
      'Content-Type': 'multipart/form-data'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(
        `/python-api/image-to-pdf`,
        formData,
        { headers }
    );

    resultFileUrl.value = response.data.id;
    resultFileId.value = response.data.id;
    operationSuccess.value = true;
    resultFilename.value = response.data.filename || 'converted.pdf';
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error converting images to PDF:', error);
    error.value = error.response?.data?.error || t('pdf.conversionError');
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
  } catch (error) {
    console.error('Error downloading file:', error);
    error.value = t('pdf.downloadError');
  }
};

// Clean up preview URLs when component is destroyed
onBeforeUnmount(() => {
  Object.values(imagePreviewUrls.value).forEach(url => {
    URL.revokeObjectURL(url);
  });
});
</script>