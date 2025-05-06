<template>
  <v-card class="pa-4">
    <v-card-title class="text-center">
      {{ $t('pdf.upload') }}
    </v-card-title>
    <v-card-text>
      <v-file-input
          v-model="file"
          :label="$t('pdf.selectFile')"
          accept="application/pdf"
          prepend-icon="mdi-file-pdf-box"
          @change="handleFileChange"
      />

      <div class="text-center mt-4">
        <v-btn
            color="primary"
            :disabled="!file"
            @click="uploadFile"
        >
          {{ $t('pdf.upload') }}
        </v-btn>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['file-uploaded'])

const file = ref(null)

const handleFileChange = () => {
  if (file.value) {
    emit('file-uploaded', file.value)
  }
}

const uploadFile = () => {
  if (file.value) {
    emit('file-uploaded', file.value)
  }
}
</script>