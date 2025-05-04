<template>
  <v-menu>
    <template v-slot:activator="{ props }">
      <v-btn icon v-bind="props">
        <v-icon>mdi-translate</v-icon>
      </v-btn>
    </template>
    <v-list>
      <v-list-item
          v-for="lang in languages"
          :key="lang.code"
          @click="changeLanguage(lang.code)"
      >
        <v-list-item-title>{{ lang.name }}</v-list-item-title>
      </v-list-item>
    </v-list>
  </v-menu>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const { locale } = useI18n()

const languages = [
  { code: 'sk', name: 'Slovenčina' },
  { code: 'en', name: 'English' }
]

const changeLanguage = (code) => {
  locale.value = code
  localStorage.setItem('language', code)
}
</script>