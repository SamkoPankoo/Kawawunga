<template>
  <v-card>
    <v-card-title class="d-flex justify-space-between align-center">
      <span>PDF Viewer</span>
      <div>
        <v-btn icon @click="currentPage--" :disabled="currentPage <= 0">
          <v-icon>mdi-chevron-left</v-icon>
        </v-btn>
        <span class="mx-2">{{ currentPage + 1 }} / {{ numPages }}</span>
        <v-btn icon @click="currentPage++" :disabled="currentPage >= numPages - 1">
          <v-icon>mdi-chevron-right</v-icon>
        </v-btn>
      </div>
    </v-card-title>
    <v-card-text>
      <div ref="pdfContainer" class="pdf-container">
        <vue-pdf-embed
            :source="pdfUrl"
            :page="currentPage + 1"
            @loaded="handleLoaded"
            @rendered="handleRendered"
            @render-failed="handleRenderFailed"
        />
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref, watch } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'

const props = defineProps({
  pdfUrl: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['page-selected'])

const currentPage = ref(0)
const numPages = ref(0)
const pdfContainer = ref(null)

const handleLoaded = (event) => {
  numPages.value = event.numPages
}

const handleRendered = () => {
  if (pdfContainer.value) {
    pdfContainer.value.scrollTop = 0 // Scroll to top after rendering
  }
  console.log('PDF rendered successfully')
}

const handleRenderFailed = (error) => {
  console.error('PDF render failed:', error)
}

watch(currentPage, (newPage) => {
  emit('page-selected', newPage + 1)
})
</script>

<style scoped>
.pdf-container {
  width: 100%;
  min-height: 600px;
  overflow: auto;
}
</style>