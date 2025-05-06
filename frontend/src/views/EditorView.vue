<template>
  <v-container>
    <v-row>
      <v-col cols="12" class="text-center">
        <h1 class="text-h3 mb-6">{{ $t('pdf.toolTitle') }}</h1>
        <p class="text-subtitle-1 mb-8">{{ $t('pdf.toolSubtitle') }}</p>
      </v-col>
    </v-row>

    <v-row>
      <v-col v-for="tool in pdfTools" :key="tool.id" cols="12" sm="6" md="4" lg="3">
        <v-card
            :to="tool.route"
            height="100%"
            class="d-flex flex-column tool-card"
            hover
            elevation="2"
        >
          <v-card-title class="text-center">
            <v-icon size="48" color="primary" class="mb-2">{{ tool.icon }}</v-icon>
            <div class="text-h6">{{ $t(tool.title) }}</div>
          </v-card-title>
          <v-card-text class="text-center">
            <p>{{ $t(tool.description) }}</p>
          </v-card-text>
          <v-spacer></v-spacer>
          <v-card-actions class="justify-center mb-2">
            <v-btn color="primary" variant="outlined">
              {{ $t('common.use') }}
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue';

const pdfTools = ref([
  {
    id: 1,
    icon: 'mdi-file-link',
    title: 'pdf.mergePdf',
    description: 'pdf.mergePdfDesc',
    route: '/editor/merge'
  },
  {
    id: 2,
    icon: 'mdi-rotate-right',
    title: 'pdf.rotatePdf',
    description: 'pdf.rotatePdfDesc',
    route: '/editor/rotate'
  },
  {
    id: 3,
    icon: 'mdi-file-split',
    title: 'pdf.splitPdf',
    description: 'pdf.splitPdfDesc',
    route: '/editor/split'
  },
  {
    id: 4,
    icon: 'mdi-format-color-highlight',
    title: 'pdf.watermarkPdf',
    description: 'pdf.watermarkPdfDesc',
    route: '/editor/watermark'
  },
  {
    id: 5,
    icon: 'mdi-file-remove',
    title: 'pdf.deletePages',
    description: 'pdf.deletePagesDesc',
    route: '/editor/delete-pages'
  }
]);
</script>

<style scoped>
.tool-card {
  transition: transform 0.2s;
}
.tool-card:hover {
  transform: translateY(-5px);
}
</style>