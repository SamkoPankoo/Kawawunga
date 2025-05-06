<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.mergePdf') }}
          </v-card-title>
          <v-card-text>
            <p class="mb-4">{{ $t('pdf.mergePdfDesc') }}</p>

            <v-file-input
                v-model="selectedFiles"
                :label="$t('pdf.dropFilesHere')"
                accept="application/pdf"
                multiple
                chips
                prepend-icon="mdi-file-pdf-box"
                @change="handleFileSelection"
                :rules="[rules.required]"
                counter
            ></v-file-input>

            <v-list v-if="selectedFiles.length > 0" class="mb-4 border rounded">
              <div class="d-flex align-center px-4 py-2 bg-grey-lighten-4">
                <h3 class="text-subtitle-1">{{ $t('pdf.selectedFiles') }}</h3>
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
                  <v-icon color="primary">mdi-file-pdf-box</v-icon>
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
          <v-card-actions class="px-4 pb-4">
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                :disabled="!selectedFiles.length || selectedFiles.length < 2 || loading"
                :loading="loading"
                @click="mergePdfs"
                prepend-icon="mdi-file-link"
                size="large"
            >
              {{ $t('pdf.merge') }}
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
          <p class="text-grey">{{ mergedFileName }}</p>
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
import { ref } from 'vue';
import axios from 'axios';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const selectedFiles = ref([]);
const selectedFileIndex = ref(null);
const loading = ref(false);
const showResultDialog = ref(false);
const resultFileUrl = ref(null);
const error = ref(null);
const mergedFileName = ref('merged.pdf');

const rules = {
  required: value => !!value && value.length > 0 || t('validation.required')
};

const handleFileSelection = () => {
  if (selectedFiles.value.length > 0) {
    selectedFileIndex.value = 0;
    error.value = null;
  } else {
    selectedFileIndex.value = null;
  }
};

const removeFile = (index) => {
  selectedFiles.value.splice(index, 1);
  if (selectedFileIndex.value === index) {
    selectedFileIndex.value = selectedFiles.value.length > 0 ? 0 : null;
  } else if (selectedFileIndex.value > index) {
    selectedFileIndex.value--;
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

const mergePdfs = async () => {
  if (selectedFiles.value.length < 2) {
    error.value = t('pdf.needMinTwoFiles');
    return;
  }

  loading.value = true;
  error.value = null;

  try {
    const formData = new FormData();
    selectedFiles.value.forEach((file, index) => {
      formData.append(`file${index + 1}`, file);
    });

    // Generate a meaningful name for the merged file
    if (selectedFiles.value.length === 2) {
      const fileName1 = selectedFiles.value[0].name.replace('.pdf', '');
      const fileName2 = selectedFiles.value[1].name.replace('.pdf', '');
      mergedFileName.value = `${fileName1}_${fileName2}.pdf`;
    } else {
      mergedFileName.value = `merged_${selectedFiles.value.length}_files.pdf`;
    }

    formData.append('output_filename', mergedFileName.value);

    const response = await axios.post(
        `${import.meta.env.VITE_PYTHON_API_URL}/merge`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        }
    );

    resultFileUrl.value = response.data.id;
    showResultDialog.value = true;
  } catch (error) {
    console.error('Error merging PDFs:', error);
    error.value = error.response?.data?.error || t('pdf.mergeError');
  } finally {
    loading.value = false;
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
    link.setAttribute('download', mergedFileName.value);
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('Error downloading merged PDF:', error);
    error.value = t('pdf.downloadError');
  }
};
</script>

<style scoped>
.selected-file {
  background-color: rgba(var(--v-theme-primary), 0.1);
}
</style>