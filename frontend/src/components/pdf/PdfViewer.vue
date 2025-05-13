<template>
  <v-card>
    <v-card-title class="d-flex justify-space-between align-center">
      <span>{{ $t('pdf.viewer') }}</span>
      <div>
        <v-btn icon @click="prevPage" :disabled="currentPage <= 1">
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>
        <span class="mx-2">{{ currentPage }} / {{ numPages }}</span>
        <v-btn icon @click="nextPage" :disabled="currentPage >= numPages">
          <v-icon>mdi-chevron-right</v-icon>
        </v-btn>
      </div>
    </v-card-title>
    <v-card-text>
      <div ref="pdfContainer" class="pdf-container">
        <pdf
            v-if="pdfUrl"
            :src="pdfUrl"
            :page="currentPage"
            @num-pages="numPages = $event"
            @page-loaded="pageLoaded"
            @error="handleError"
        ></pdf>
        <v-progress-circular
            v-if="loading"
            indeterminate
            color="primary"
            class="mt-5"
        ></v-progress-circular>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue';
import PdfEmbed from 'vue-pdf-embed';

const props = defineProps({
  pdfUrl: {
    type: String,
    required: true
  }
});

const emit = defineEmits(['page-selected']);

const currentPage = ref(1);
const numPages = ref(0);
const pdfContainer = ref(null);
const loading = ref(true);

const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--;
  }
};

const nextPage = () => {
  if (currentPage.value < numPages.value) {
    currentPage.value++;
  }
};

const pageLoaded = () => {
  if (pdfContainer.value) {
    pdfContainer.value.scrollTop = 0;
  }
  loading.value = false;
  console.log('PDF page loaded successfully');
};

const handleError = (error) => {
  loading.value = false;
  console.error('PDF loading error:', error);
};

watch(currentPage, (newPage) => {
  emit('page-selected', newPage);
  loading.value = true;
});
</script>

<style scoped>
.pdf-container {
  width: 100%;
  min-height: 600px;
  overflow: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}
</style>