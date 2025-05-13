<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.rotatePdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.rotatePdfDesc') }}</p>

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
          <v-card-title>{{ $t('pdf.rotateOptions') }}</v-card-title>
          <v-card-text>
            <h3 class="text-subtitle-1 font-weight-bold mb-2">{{ $t('pdf.rotationAngle') }}</h3>
            <v-radio-group
                v-model="rotationAngle"
                mandatory
                class="mb-4"
            >
              <v-radio
                  :label="$t('pdf.rotate90')"
                  :value="90"
              ></v-radio>
              <v-radio
                  :label="$t('pdf.rotate180')"
                  :value="180"
              ></v-radio>
              <v-radio
                  :label="$t('pdf.rotate270')"
                  :value="270"
              ></v-radio>
            </v-radio-group>

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

            <template v-if="pageSelection === 'select'">
              <p class="text-body-2 mb-2">{{ $t('pdf.selectPagesToRotate') }}</p>
              <v-row>
                <v-col v-for="page in numPages" :key="page" cols="3" sm="2" class="text-center">
                  <v-checkbox
                      v-model="selectedPages"
                      :value="page"
                      :label="page.toString()"
                      hide-details
                      density="compact"
                  ></v-checkbox>
                </v-col>
              </v-row>
              <p class="text-caption mt-2">{{ $t('pdf.selectedPagesCount', { count: selectedPages.length }) }}</p>
            </template>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canRotatePages || rotating"
                :loading="rotating"
                @click="rotatePages"
                prepend-icon="mdi-rotate-right"
                size="large"
            >
              {{ $t('pdf.rotatePage') }}
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
          <p>{{ $t('pdf.fileProcessed') }}</p>
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

const { t } = useI18n();

const selectedFile = ref(null);
const pdfUrl = ref(null);
const pdfInfo = ref(null);
const currentPage = ref(1);
const numPages = ref(0);
const loading = ref(false);
const error = ref(null);
const fileId = ref(null);

// Rotation options
const rotationAngle = ref(90);
const pageSelection = ref('all');
const pageRange = ref({ from: 1, to: 1 });
const customPages = ref('');
const selectedPages = ref([]);
const rotating = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);

const pageSelectionOptions = computed(() => [
  { title: t('pdf.allPages'), value: 'all' },
  { title: t('pdf.currentPage'), value: 'current' },
  { title: t('pdf.pageRange'), value: 'range' },
  { title: t('pdf.customPages'), value: 'custom' },
  { title: t('pdf.selectPagesOption'), value: 'select' }
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

const canRotatePages = computed(() => {
  if (!pdfInfo.value) return false;

  if (pageSelection.value === 'range') {
    const start = parseInt(pageRange.value.from);
    const end = parseInt(pageRange.value.to);
    return !isNaN(start) && !isNaN(end) && start >= 1 && end <= numPages.value && start <= end;
  }

  if (pageSelection.value === 'custom') {
    return validateCustomPages(customPages.value) === true;
  }

  if (pageSelection.value === 'select') {
    return selectedPages.value.length > 0;
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
  } else if (pageSelection.value === 'select') {
    selectedPages.value = [currentPage.value];
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

const rotatePages = async () => {
  if (!fileId.value) return;

  rotating.value = true;
  error.value = null;

  try {
    let pages = [];
    let pageRanges = [];

    if (pageSelection.value === 'all') {
      // No need for explicit pages, we'll rotate all
    } else if (pageSelection.value === 'current') {
      pages = [currentPage.value];
    } else if (pageSelection.value === 'range') {
      pageRanges = [{
        start: parseInt(pageRange.value.from),
        end: parseInt(pageRange.value.to)
      }];
    } else if (pageSelection.value === 'custom') {
      pages = customPages.value.split(',').map(p => parseInt(p.trim()));
    } else if (pageSelection.value === 'select') {
      pages = [...selectedPages.value];
    }

    const requestData = {
      file_id: fileId.value,
      angle: rotationAngle.value,
      page_selection: pageSelection.value,
      pages: pages,
      page_ranges: pageRanges
    };

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/rotate`,
        requestData
    );

    resultFileUrl.value = response.data.id;
    resultFilename.value = response.data.filename || 'rotated.pdf';
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error rotating PDF:', error);
    error.value = error.response?.data?.error || t('pdf.rotateError');
  } finally {
    rotating.value = false;
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

// Inicializácia
updatePageRange();
</script>