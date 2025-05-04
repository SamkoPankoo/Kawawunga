<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <PdfToolbar @action="handleAction" />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8">
        <PdfViewer
            v-if="currentPdf"
            :pdf-url="currentPdf"
            @page-selected="selectedPage = $event"
        />
        <PdfUploader v-else @file-uploaded="handleFileUpload" />
      </v-col>

      <v-col cols="12" md="4">
        <v-card>
          <v-card-title>{{ $t('pdf.tools') }}</v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item @click="rotatePage">
                <v-list-item-title>{{ $t('pdf.rotatePage') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="deletePage">
                <v-list-item-title>{{ $t('pdf.deletePage') }}</v-list-item-title>
              </v-list-item>
              <v-list-item @click="showMergeDialog = true">
                <v-list-item-title>{{ $t('pdf.merge') }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Merge Dialog -->
    <v-dialog v-model="showMergeDialog" max-width="500">
      <v-card>
        <v-card-title>{{ $t('pdf.merge') }}</v-card-title>
        <v-card-text>
          <v-file-input
              v-model="mergeFile"
              :label="$t('pdf.selectFile')"
              accept="application/pdf"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn @click="showMergeDialog = false">{{ $t('common.cancel') }}</v-btn>
          <v-btn color="primary" @click="mergePdfs">{{ $t('pdf.merge') }}</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import PdfToolbar from '../components/pdf/PdfToolbar.vue'
import PdfViewer from '../components/pdf/PdfViewer.vue'
import PdfUploader from '../components/pdf/PdfUploader.vue'
import { usePdfStore } from '../stores/pdf'

const pdfStore = usePdfStore()

const currentPdf = ref(null)
const selectedPage = ref(0)
const showMergeDialog = ref(false)
const mergeFile = ref(null)

const handleFileUpload = (file) => {
  currentPdf.value = URL.createObjectURL(file)
  pdfStore.setCurrentPdf(file)
}

const handleAction = (action) => {
  switch (action) {
    case 'save':
      savePdf()
      break
    case 'download':
      downloadPdf()
      break
  }
}

const rotatePage = async () => {
  if (!selectedPage.value) return
  await pdfStore.rotatePage(selectedPage.value)
}

const deletePage = async () => {
  if (!selectedPage.value) return
  await pdfStore.deletePage(selectedPage.value)
}

const mergePdfs = async () => {
  if (!mergeFile.value) return
  await pdfStore.mergePdfs(mergeFile.value)
  showMergeDialog.value = false
}

const savePdf = async () => {
  await pdfStore.savePdf()
}

const downloadPdf = () => {
  pdfStore.downloadPdf()
}
</script>