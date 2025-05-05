<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('pdf.featureTitle') }}
          </v-card-title>
          <v-card-text>
            <p>{{ $t('pdf.featureDesc') }}</p>
            <v-alert type="info">
              Táto funkcia je momentálne vo vývoji.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
// Placeholder komponent
</script>