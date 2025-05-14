<template>
  <v-form @submit.prevent="handleSubmit" ref="form">
    <v-text-field
        v-model="formData.email"
        :label="$t('auth.email')"
        :rules="[rules.required, rules.email]"
        type="email"
        prepend-icon="mdi-email"
    />

    <v-text-field
        v-model="formData.password"
        :label="$t('auth.password')"
        :rules="[rules.required]"
        :type="showPassword ? 'text' : 'password'"
        prepend-icon="mdi-lock"
        :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
        @click:append="showPassword = !showPassword"
    />

    <v-alert v-if="error" type="error" class="mb-4">
      {{ error }}
    </v-alert>

    <v-btn
        type="submit"
        color="primary"
        block
        :loading="loading"
    >
      {{ $t('auth.loginButton') }}
    </v-btn>

    <div class="text-center mt-4">
      <router-link to="/register">
        {{ $t('auth.noAccount') }}
      </router-link>
    </div>
  </v-form>
</template>

<script setup>
import {ref} from 'vue'
import {useRouter} from 'vue-router'

import {useI18n} from 'vue-i18n'
import {useAuthStore} from "@/stores/auth.js";

const router = useRouter()
const authStore = useAuthStore()
const {t} = useI18n()

const form = ref(null)
const loading = ref(false)
const error = ref('')
const showPassword = ref(false)

const formData = ref({
  email: '',
  password: ''
})

const rules = {
  required: value => !!value || t('validation.required'),
  email: value => /.+@.+\..+/.test(value) || t('validation.email')
}

const handleSubmit = async () => {
  const {valid} = await form.value.validate()
  if (!valid) return

  loading.value = true
  error.value = ''

  try {
    await authStore.login(formData.value)
    router.push('/dashboard')
  } catch (err) {
    error.value = err.response?.data?.message || t('auth.loginError')
  } finally {
    loading.value = false
  }
}
</script>