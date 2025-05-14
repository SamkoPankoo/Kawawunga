<template>
  <!-- This is a functional component with no UI -->
</template>

<script setup>
import { ref, onMounted } from 'vue';
import historyService from '@/services/historyService';
import { useAuthStore } from '@/stores/auth';

const authStore = useAuthStore();

const props = defineProps({
  operation: {
    type: String,
    required: true
  },
  description: {
    type: String,
    default: ''
  },
  metadata: {
    type: Object,
    default: () => ({})
  },
  autoLog: {
    type: Boolean,
    default: true
  }
});

const emit = defineEmits(['logged', 'error']);

const isLogged = ref(false);
const error = ref(null);

// Method to log the operation
const logOperation = async () => {
  try {
    // Check if we have authentication credentials
    if (!authStore.isAuthenticated || (!authStore.token && !authStore.user?.apiKey)) {
      console.warn("No authentication credentials available, cannot log operation");
      emit('error', { error: 'Missing authentication credentials' });
      return false;
    }

    // Use the history service to log the operation
    const success = await historyService.logPdfOperation(
        props.operation,
        props.description,
        props.metadata
    );

    isLogged.value = success;
    if (success) {
      emit('logged', { operation: props.operation });
    } else {
      error.value = 'Failed to log operation';
      emit('error', { error: 'Failed to log operation' });
    }
    return success;
  } catch (err) {
    error.value = err.message;
    emit('error', { error: err.message });
    return false;
  }
};

// Automatically log when component is mounted if autoLog=true
onMounted(() => {
  if (props.autoLog) {
    logOperation();
  }
});

// Expose the logOperation method for manual logging
defineExpose({
  logOperation
});
</script>