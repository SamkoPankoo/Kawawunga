<template>
  <v-container class="fill-height">
    <v-row justify="center">
      <v-col cols="12" sm="8" md="6">
        <v-card>
          <v-card-title class="text-h5">
            {{ $t('common.register') }}
          </v-card-title>
          <v-card-text>
            <RegisterForm />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import RegisterForm from '../components/auth/RegisterForm.vue'
</script>