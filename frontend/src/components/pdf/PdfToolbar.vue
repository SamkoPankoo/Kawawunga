<template>
  <v-toolbar dense color="grey-lighten-4">
    <v-btn
        variant="text"
        @click="emit('action', 'save')"
    >
      <v-icon left>mdi-content-save</v-icon>
      {{ $t('pdf.save') }}
    </v-btn>

    <v-btn
        variant="text"
        @click="emit('action', 'download')"
    >
      <v-icon left>mdi-download</v-icon>
      {{ $t('pdf.download') }}
    </v-btn>

    <v-spacer></v-spacer>

    <v-btn
        variant="text"
        @click="emit('action', 'new')"
    >
      <v-icon left>mdi-file-document-plus</v-icon>
      {{ $t('pdf.newDocument') }}
    </v-btn>
  </v-toolbar>
</template>

<script setup>
const emit = defineEmits(['action'])
</script>