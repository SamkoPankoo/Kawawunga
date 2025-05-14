<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.splitPdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.splitPdfDesc') }}</p>

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
          <v-card-title>{{ $t('pdf.viewer') }}</v-card-title>
          <v-card-text>
            <vue-pdf-embed
                v-if="pdfUrl"
                :source="pdfUrl"
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
          <v-card-title>{{ $t('pdf.splitOptions') }}</v-card-title>
          <v-card-text>
            <v-radio-group v-model="splitMethod" mandatory>
              <v-radio
                  :label="$t('pdf.splitByPage')"
                  value="byPage"
              ></v-radio>
              <v-radio
                  :label="$t('pdf.splitByRanges')"
                  value="byRanges"
              ></v-radio>
              <v-radio
                  :label="$t('pdf.extractPages')"
                  value="extractPages"
              ></v-radio>
            </v-radio-group>

            <template v-if="splitMethod === 'byPage'">
              <p class="text-body-2 mb-2">{{ $t('pdf.eachPageSeparate') }}</p>
            </template>

            <template v-if="splitMethod === 'byRanges'">
              <p class="text-body-2 mb-2">{{ $t('pdf.defineRanges') }}</p>

              <div v-for="(range, index) in pageRanges" :key="index" class="d-flex mb-2">
                <v-text-field
                    v-model="range.start"
                    type="number"
                    :label="$t('pdf.from')"
                    min="1"
                    :max="numPages"
                    class="mr-2"
                    :rules="[rules.required, rules.validPage]"
                    density="compact"
                ></v-text-field>
                <v-text-field
                    v-model="range.end"
                    type="number"
                    :label="$t('pdf.to')"
                    min="1"
                    :max="numPages"
                    class="mr-2"
                    :rules="[rules.required, rules.validPage, validateRange(range)]"
                    density="compact"
                ></v-text-field>
                <v-btn
                    icon="mdi-delete"
                    color="error"
                    size="small"
                    variant="text"
                    @click="removeRange(index)"
                    :disabled="pageRanges.length <= 1"
                ></v-btn>
              </div>

              <v-btn
                  prepend-icon="mdi-plus"
                  size="small"
                  class="mt-2"
                  @click="addRange"
                  variant="outlined"
              >
                {{ $t('pdf.addRange') }}
              </v-btn>
            </template>

            <template v-if="splitMethod === 'extractPages'">
              <p class="text-body-2 mb-2">{{ $t('pdf.extractPagesDesc') }}</p>
              <v-text-field
                  v-model="extractPages"
                  :label="$t('pdf.pageNumbers')"
                  :hint="$t('pdf.pageNumbersHint')"
                  :rules="[rules.required, validateExtractPages]"
                  class="mb-2"
              ></v-text-field>
            </template>

            <v-switch
                v-model="createZipFile"
                :label="$t('pdf.createZipFile')"
                class="mt-4"
            ></v-switch>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canSplit || splitting"
                :loading="splitting"
                @click="splitPdf"
                prepend-icon="mdi-file-split"
                size="large"
            >
              {{ $t('pdf.split') }}
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
          <p>{{ $t('pdf.filesProcessed') }}</p>
          <p class="text-grey" v-if="resultFiles.length === 1">{{ resultFiles[0].filename }}</p>
          <v-list v-else-if="resultFiles.length > 1" density="compact" class="bg-grey-lighten-4 rounded mt-2">
            <v-list-item
                v-for="(file, index) in resultFiles"
                :key="index"
                :title="file.filename"
            >
              <template v-slot:prepend>
                <v-icon color="primary">mdi-file-pdf-box</v-icon>
              </template>
            </v-list-item>
          </v-list>
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
        :operation="'split'"
        :description="getLogDescription()"
        :metadata="getLogMetadata()"
        @logged="handleLogged"
        @error="handleLogError"
    />
  </v-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

import VuePdfEmbed from 'vue-pdf-embed';
import LogOperation from '@/components/pdf/LogOperation.vue';
const operationSuccess = ref(false);
const resultFileId = ref(null);

const { t } = useI18n();
import { useAuthStore } from '@/stores/auth';


const selectedFile = ref(null);
const pdfUrl = ref(null);
const pdfInfo = ref(null);
const currentPage = ref(1);
const numPages = ref(0);
const loading = ref(false);
const error = ref(null);
const fileId = ref(null);

const splitMethod = ref('byPage');
const pageRanges = ref([{ start: 1, end: 1 }]);
const extractPages = ref('');
const createZipFile = ref(true);

const splitting = ref(false);
const showResultDialog = ref(false);
const resultFiles = ref([]);

const rules = {
  required: value => !!value || t('validation.required'),
  validPage: value => {
    const page = parseInt(value);
    return (page >= 1 && page <= numPages.value) || t('validation.pageRange', { max: numPages.value });
  }
};

const validateRange = (range) => {
  return () => {
    const start = parseInt(range.start);
    const end = parseInt(range.end);
    return start <= end || t('validation.startEndOrder');
  };
};

const validateExtractPages = (value) => {
  if (!value) return true;

  const pagePattern = /^(\d+)(,\s*\d+)*$/;
  if (!pagePattern.test(value)) {
    return t('validation.extractPagesFormat');
  }

  const pages = value.split(',').map(p => parseInt(p.trim()));
  const invalidPages = pages.filter(p => p < 1 || p > numPages.value);

  if (invalidPages.length > 0) {
    return t('validation.invalidPages', { pages: invalidPages.join(', '), max: numPages.value });
  }

  return true;
};

const canSplit = computed(() => {
  if (!pdfInfo.value) return false;

  if (splitMethod.value === 'byRanges') {
    return pageRanges.value.every(range => {
      const start = parseInt(range.start);
      const end = parseInt(range.end);
      return !isNaN(start) && !isNaN(end) && start >= 1 && end <= numPages.value && start <= end;
    });
  }

  if (splitMethod.value === 'extractPages') {
    return validateExtractPages(extractPages.value) === true;
  }

  return true;
});

watch(numPages, (newValue) => {
  if (newValue > 0) {
    pageRanges.value[0].end = newValue;
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


const getLogDescription = () => {
  let desc = '';
  if (splitMethod.value === 'byPage') {
    desc = `Split PDF into ${numPages.value} individual pages`;
  } else if (splitMethod.value === 'byRanges') {
    desc = `Split PDF into ${pageRanges.value.length} ranges`;
  } else if (splitMethod.value === 'extractPages') {
    const pageCount = extractPages.value.split(',').length;
    desc = `Extracted ${pageCount} pages from PDF`;
  }
  return desc;
};

const getLogMetadata = () => {
  return {
    fileName: selectedFile.value?.name,
    splitMethod: splitMethod.value,
    resultFiles: resultFiles.value.map(f => f.filename),
    fileCount: resultFiles.value.length,
    timestamp: new Date().toISOString()
  };
};

// Within splitPdf function (after getting results)
if (resultFiles.value.length > 0 && resultFiles.value[0].id) {
  resultFileId.value = resultFiles.value[0].id;
  operationSuccess.value = true;
}
const handleLogged = () => {
  console.log('Operation logged successfully');
};

const handleLogError = (error) => {
  console.error('Failed to log operation:', error);
};
const pageLoaded = () => {
  loading.value = false;
};

const handleError = (error) => {
  console.error('PDF error:', error);
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

const addRange = () => {
  pageRanges.value.push({ start: 1, end: numPages.value });
};

const removeRange = (index) => {
  if (pageRanges.value.length > 1) {
    pageRanges.value.splice(index, 1);
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
  } catch (error) {
    console.error('Error uploading PDF:', error);
    error.value = error.response?.data?.error || t('pdf.uploadError');
  } finally {
    loading.value = false;
  }
};

const splitPdf = async () => {
  if (!fileId.value) return;

  splitting.value = true;
  error.value = null;

  try {
    // Import auth store if not already imported

    const authStore = useAuthStore();

    let requestData = {
      file_id: fileId.value,
      split_method: splitMethod.value,
      create_zip: createZipFile.value
    };

    if (splitMethod.value === 'byRanges') {
      requestData.ranges = pageRanges.value;
    } else if (splitMethod.value === 'extractPages') {
      requestData.pages = extractPages.value.split(',').map(p => parseInt(p.trim()));
    }

    // Add API key to the request if available
    const headers = {
      'Content-Type': 'application/json'
    };

    if (authStore.user?.apiKey) {
      headers['X-API-Key'] = authStore.user.apiKey;
    }

    const response = await axios.post(
        `/python-api/split`,
        requestData,
        { headers }
    );

    if (response.data.files) {
      resultFiles.value = response.data.files;
    } else if (response.data.file) {
      resultFiles.value = [response.data.file];
    }

    // Set the success state to trigger logging
    if (resultFiles.value.length > 0 && resultFiles.value[0].id) {
      resultFileId.value = resultFiles.value[0].id;
      operationSuccess.value = true;
    }

    showResultDialog.value = true;
  } catch (error) {
    console.error('Error splitting PDF:', error);
    error.value = error.response?.data?.error || t('pdf.splitError');
  } finally {
    splitting.value = false;
  }
};


const downloadResult = async () => {
  if (resultFiles.value.length === 0) return;

  try {
    if (resultFiles.value.length === 1 || !createZipFile.value) {
      // Download a single file
      const fileId = resultFiles.value[0].id;
      const fileName = resultFiles.value[0].filename;

      const response = await axios.get(
          `/python-api/download/${fileId}`,
          { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', fileName);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } else {
      // Download zip file
      const response = await axios.get(
          `/python-api/download-zip/${resultFiles.value[0].zip_id}`,
          { responseType: 'blob' }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'split_files.zip');
      document.body.appendChild(link);
      link.click();
      link.remove();
    }
  } catch (error) {
    console.error('Error downloading files:', error);
    error.value = t('pdf.downloadError');
  }
};
</script>