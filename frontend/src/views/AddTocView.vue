<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.addToc') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.addTocDesc') }}</p>

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
          <v-card-title>{{ $t('pdf.tocOptions') }}</v-card-title>
          <v-card-text>
            <div v-for="(entry, index) in tocEntries" :key="index" class="mb-4">
              <div class="d-flex align-center">
                <span class="text-subtitle-1 mr-2">{{ $t('pdf.tocEntry') }} #{{ index + 1 }}</span>
                <v-spacer></v-spacer>
                <v-btn
                    icon="mdi-delete"
                    size="small"
                    variant="text"
                    color="error"
                    @click="removeEntry(index)"
                ></v-btn>
              </div>

              <v-text-field
                  v-model="entry.title"
                  :label="$t('pdf.entryTitle')"
                  class="mb-2"
                  :rules="[rules.required]"
              ></v-text-field>

              <v-text-field
                  v-model="entry.page"
                  :label="$t('pdf.pageNumber')"
                  type="number"
                  :min="1"
                  :max="numPages"
                  :rules="[rules.required, rules.validPage]"
              ></v-text-field>
            </div>

            <v-btn
                block
                variant="outlined"
                color="primary"
                prepend-icon="mdi-plus"
                @click="addEntry"
                class="mt-4"
            >
              {{ $t('pdf.addEntry') }}
            </v-btn>

            <v-alert
                type="info"
                variant="tonal"
                class="mt-6"
                icon="mdi-information"
            >
              {{ $t('pdf.tocInfo') }}
            </v-alert>
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!canAddToc || processing"
                :loading="processing"
                @click="addToc"
                prepend-icon="mdi-view-list"
                size="large"
            >
              {{ $t('pdf.createToc') }}
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
          <p>{{ $t('pdf.tocAdded') }}</p>
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

// TOC options
const tocEntries = ref([
  { title: '', page: 1 }
]);
const processing = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const resultFilename = ref(null);

const rules = {
  required: value => !!value || t('validation.required'),
  validPage: value => {
    const page = parseInt(value);
    return (page >= 1 && page <= numPages.value) || t('validation.pageRange', { max: numPages.value });
  }
};

const canAddToc = computed(() => {
  return pdfInfo.value &&
      tocEntries.value.length > 0 &&
      tocEntries.value.every(entry => entry.title.trim() !== '' && entry.page >= 1);
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

const addEntry = () => {
  tocEntries.value.push({ title: '', page: 1 });
};

const removeEntry = (index) => {
  tocEntries.value.splice(index, 1);
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

const addToc = async () => {
  if (!fileId.value) return;

  processing.value = true;
  error.value = null;

  try {
    // Clean and format TOC entries
    const validEntries = tocEntries.value
        .filter(entry => entry.title.trim() !== '')
        .map(entry => ({
          title: entry.title.trim(),
          page: parseInt(entry.page)
        }));

    const requestData = {
      file_id: fileId.value,
      toc_entries: validEntries
    };

    const headers = {
      'Content-Type': 'application/json'
    };

    // Add API key if user is authenticated
    if (authStore.token) {
      headers['X-API-Key'] = authStore.user?.apiKey;
    }

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/add-toc`,
        requestData,
        { headers }
    );

    resultFileUrl.value = response.data.id;
    resultFilename.value = response.data.filename || 'with_toc.pdf';
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error adding TOC:', error);
    error.value = error.response?.data?.error || t('pdf.tocError');
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