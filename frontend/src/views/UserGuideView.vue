<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title class="d-flex align-center">
            <div class="text-h4">{{ $t('userGuide.title') }}</div>
            <v-spacer></v-spacer>
            <v-btn
                color="primary"
                prepend-icon="mdi-file-pdf-box"
                @click="downloadPdf"
                :loading="loading"
            >
              {{ $t('userGuide.downloadPdf') }}
            </v-btn>
          </v-card-title>
        </v-card>
      </v-col>
    </v-row>

    <div id="user-guide-content">
      <v-row>
        <!-- Navigation -->
        <v-col cols="12" md="3">
          <v-card>
            <v-list nav>
              <v-list-item
                  v-for="section in sections"
                  :key="section.id"
                  :value="section.id"
                  :href="'#' + section.id"
                  @click.prevent="scrollToSection(section.id)"
              >
                <v-list-item-title>{{ $t(section.title) }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-card>
        </v-col>

        <!-- Content -->
        <v-col cols="12" md="9">
          <v-card>
            <v-card-text class="content-container">
              <!-- Introduction -->
              <section :id="sections[0].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.introduction') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.introText') }}</p>
                <p class="text-body-1">{{ $t('userGuide.introDescription') }}</p>
                <v-img
                    src="@/assets/intro-image.png"
                    alt="PDF Editor Interface"
                    class="my-4"
                    contain
                    max-height="300"
                ></v-img>
              </section>

              <!-- Getting Started -->
              <section :id="sections[1].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.gettingStarted') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.gettingStartedText') }}</p>

                <div class="section-content">
                  <h3 class="text-h5 mt-4 mb-2">{{ $t('userGuide.registration') }}</h3>
                  <ol class="text-body-1">
                    <li>{{ $t('userGuide.registrationStep1') }}</li>
                    <li>{{ $t('userGuide.registrationStep2') }}</li>
                    <li>{{ $t('userGuide.registrationStep3') }}</li>
                  </ol>

                  <h3 class="text-h5 mt-4 mb-2">{{ $t('userGuide.login') }}</h3>
                  <ol class="text-body-1">
                    <li>{{ $t('userGuide.loginStep1') }}</li>
                    <li>{{ $t('userGuide.loginStep2') }}</li>
                    <li>{{ $t('userGuide.loginStep3') }}</li>
                  </ol>

                  <h3 class="text-h5 mt-4 mb-2">{{ $t('userGuide.dashboard') }}</h3>
                  <p class="text-body-1">
                    {{ $t('userGuide.dashboardDescription') }}
                  </p>
                  <ul class="text-body-1">
                    <li>{{ $t('userGuide.recentActivityDesc') }}</li>
                    <li>{{ $t('userGuide.quickAccessDesc') }}</li>
                    <li>{{ $t('userGuide.apiAccessDesc') }}</li>
                  </ul>
                </div>
              </section>

              <!-- Features -->
              <section :id="sections[2].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.features') }}</h2>
                <p class="text-body-1">
                  PDF Editor provides the following features for working with PDF files:
                </p>

                <!-- Merge PDF -->
                <div class="mb-6">
                  <h3 class="text-h5 mb-2">{{ $t('userGuide.merge.title') }}</h3>
                  <p class="text-body-1">{{ $t('pdf.mergePdfDesc') }}</p>
                  <v-card variant="outlined" class="pa-4 my-2">
                    <h4 class="text-subtitle-1 font-weight-bold">{{ $t('userGuide.tools') }}:</h4>
                    <div class="pl-1">
                      <ol class="text-body-1 pl-4">
                        <li>{{ $t('userGuide.merge.step1') }}</li>
                        <li>{{ $t('userGuide.merge.step2') }}</li>
                        <li>{{ $t('userGuide.merge.step3') }}</li>
                        <li>{{ $t('userGuide.merge.step4') }}</li>
                        <li>{{ $t('userGuide.merge.step5') }}</li>
                      </ol>
                    </div>
                  </v-card>
                </div>

                <!-- Split PDF -->
                <div class="mb-6">
                  <h3 class="text-h5 mb-2">{{ $t('userGuide.split.title') }}</h3>
                  <p class="text-body-1">{{ $t('pdf.splitPdfDesc') }}</p>
                  <v-card variant="outlined" class="pa-4 my-2">
                    <h4 class="text-subtitle-1 font-weight-bold">{{ $t('userGuide.tools') }}:</h4>
                    <div class="pl-1">
                      <ol class="text-body-1 pl-4">
                        <li>{{ $t('userGuide.split.step1') }}</li>
                        <li>{{ $t('userGuide.split.step2') }}</li>
                        <li>{{ $t('userGuide.split.step3') }}</li>
                        <li>{{ $t('userGuide.split.step4') }}</li>
                        <li>{{ $t('userGuide.split.step5') }}</li>
                        <li>{{ $t('userGuide.split.step6') }}</li>
                      </ol>
                    </div>
                  </v-card>
                </div>

                <!-- Watermark PDF -->
                <div class="mb-6">
                  <h3 class="text-h5 mb-2">{{ $t('userGuide.watermark.title') }}</h3>
                  <p class="text-body-1">{{ $t('pdf.watermarkPdfDesc') }}</p>
                  <v-card variant="outlined" class="pa-4 my-2">
                    <h4 class="text-subtitle-1 font-weight-bold">{{ $t('userGuide.tools') }}:</h4>
                    <div class="pl-1">
                      <ol class="text-body-1 pl-4">
                        <li>{{ $t('userGuide.watermark.step1') }}</li>
                        <li>{{ $t('userGuide.watermark.step2') }}</li>
                        <li>{{ $t('userGuide.watermark.step3') }}</li>
                        <li>{{ $t('userGuide.watermark.step4') }}</li>
                        <li>{{ $t('userGuide.watermark.step5') }}</li>
                        <li>{{ $t('userGuide.watermark.step6') }}</li>
                        <li>{{ $t('userGuide.watermark.step7') }}</li>
                      </ol>
                    </div>
                  </v-card>
                </div>

                <!-- Rotate PDF -->
                <div class="mb-6">
                  <h3 class="text-h5 mb-2">{{ $t('userGuide.rotate.title') }}</h3>
                  <p class="text-body-1">{{ $t('pdf.rotatePdfDesc') }}</p>
                  <v-card variant="outlined" class="pa-4 my-2">
                    <h4 class="text-subtitle-1 font-weight-bold">{{ $t('userGuide.tools') }}:</h4>
                    <div class="pl-1">
                      <ol class="text-body-1 pl-4">
                        <li>{{ $t('userGuide.rotate.step1') }}</li>
                        <li>{{ $t('userGuide.rotate.step2') }}</li>
                        <li>{{ $t('userGuide.rotate.step3') }}</li>
                        <li>{{ $t('userGuide.rotate.step4') }}</li>
                        <li>{{ $t('userGuide.rotate.step5') }}</li>
                        <li>{{ $t('userGuide.rotate.step6') }}</li>
                      </ol>
                    </div>
                  </v-card>
                </div>

                <!-- Delete Pages -->
                <div class="mb-6">
                  <h3 class="text-h5 mb-2">{{ $t('userGuide.deletePages.title') }}</h3>
                  <p class="text-body-1">{{ $t('pdf.deletePagesDesc') }}</p>
                  <v-card variant="outlined" class="pa-4 my-2">
                    <h4 class="text-subtitle-1 font-weight-bold">{{ $t('userGuide.tools') }}:</h4>
                    <div class="pl-1">
                      <ol class="text-body-1 pl-4">
                        <li>{{ $t('userGuide.deletePages.step1') }}</li>
                        <li>{{ $t('userGuide.deletePages.step2') }}</li>
                        <li>{{ $t('userGuide.deletePages.step3') }}</li>
                        <li>{{ $t('userGuide.deletePages.step4') }}</li>
                        <li>{{ $t('userGuide.deletePages.step5') }}</li>
                      </ol>
                    </div>
                  </v-card>
                </div>
              </section>

              <!-- API Usage -->
              <section :id="sections[3].id" class="guide-section mb-8">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.apiUsage') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.apiUsageText') }}</p>

                <h3 class="text-h5 mt-4 mb-2">{{ $t('userGuide.gettingApiKey') }}</h3>
                <p class="text-body-1">
                  {{ $t('userGuide.apiKeyDescription') }}
                </p>

                <h3 class="text-h5 mt-4 mb-2">{{ $t('userGuide.authentication') }}</h3>
                <v-card variant="outlined" class="pa-4 my-2 bg-grey-lighten-4">
                  <pre class="language-bash"><code>curl -X POST https://api.pdfeditor.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "vas@email.com", "password": "vase_heslo"}'</code></pre>
                </v-card>

                <h3 class="text-h5 mt-4 mb-2">{{ $t('userGuide.usingApi') }}</h3>
                <p class="text-body-1">
                  {{ $t('userGuide.apiRequestHeader') }}
                </p>
                <v-card variant="outlined" class="pa-4 my-2 bg-grey-lighten-4">
                  <pre class="language-bash"><code>curl -X POST https://api.pdfeditor.com/api/merge \
  -H "X-API-Key: vas_api_kluc" \
  -F "file1=@cesta/k/suboru1.pdf" \
  -F "file2=@cesta/k/suboru2.pdf"</code></pre>
                </v-card>

                <p class="text-body-1 mt-4">
                  {{ $t('userGuide.fullApiDocumentation') }}
                </p>
              </section>

              <!-- Common Issues -->
              <section :id="sections[4].id" class="guide-section">
                <h2 class="text-h4 mb-4">{{ $t('userGuide.commonIssues') }}</h2>
                <p class="text-body-1">{{ $t('userGuide.commonIssuesText') }}</p>

                <v-expansion-panels class="mt-4">
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      {{ $t('userGuide.issues.fileSizeLimit.question') }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <p class="text-body-1">{{ $t('userGuide.issues.fileSizeLimit.answer') }}</p>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      {{ $t('userGuide.issues.mergeMultipleFiles.question') }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <p class="text-body-1">{{ $t('userGuide.issues.mergeMultipleFiles.answer') }}</p>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      {{ $t('userGuide.issues.passwordProtected.question') }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <p class="text-body-1">{{ $t('userGuide.issues.passwordProtected.answer') }}</p>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      {{ $t('userGuide.issues.formattingLost.question') }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <p class="text-body-1">{{ $t('userGuide.issues.formattingLost.answer') }}</p>
                    </v-expansion-panel-text>
                  </v-expansion-panel>

                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      {{ $t('userGuide.issues.newApiKey.question') }}
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <p class="text-body-1">{{ $t('userGuide.issues.newApiKey.answer') }}</p>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </section>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>
<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '@/stores/auth';
import axios from 'axios';

const loading = ref(false);

const sections = [
  { id: 'introduction', title: 'userGuide.introduction' },
  { id: 'getting-started', title: 'userGuide.gettingStarted' },
  { id: 'features', title: 'userGuide.features' },
  { id: 'api-usage', title: 'userGuide.apiUsage' },
  { id: 'common-issues', title: 'userGuide.commonIssues' }
];

const scrollToSection = (sectionId) => {
  const element = document.getElementById(sectionId);
  if (element) {
    element.scrollIntoView({ behavior: 'smooth' });
  }
};

const downloadPdf = async () => {
  loading.value = true;

  try {
    // Dynamic loading of html2pdf.js
    await new Promise((resolve, reject) => {
      if (window.html2pdf) {
        resolve();
        return;
      }
      const script = document.createElement('script');
      script.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js';
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });

    // Get guide content
    const content = document.getElementById('user-guide-content');

    // Clone and prepare for export
    const clonedContent = content.cloneNode(true);
    clonedContent.querySelectorAll('button, .v-btn').forEach(el => {
      if (el.parentNode) el.parentNode.removeChild(el);
    });

    // Replace images with placeholders to avoid cross-origin issues
    clonedContent.querySelectorAll('img').forEach(img => {
      const placeholder = document.createElement('div');
      placeholder.style.width = '100%';
      placeholder.style.height = '100px';
      placeholder.style.backgroundColor = '#f0f0f0';
      placeholder.style.display = 'flex';
      placeholder.style.alignItems = 'center';
      placeholder.style.justifyContent = 'center';
      placeholder.textContent = '[Image: ' + (img.alt || 'PDF Editor') + ']';
      if (img.parentNode) img.parentNode.replaceChild(placeholder, img);
    });

    // PDF options
    const options = {
      margin: 10,
      filename: 'pdfeditor-user-guide.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: {
        scale: 2,
        logging: false,
        useCORS: false,
        allowTaint: true
      },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
    };

    // Generate PDF
    await window.html2pdf().from(clonedContent).set(options).save();

    // Log operation
    try {
      const authStore = useAuthStore();
      if (authStore.isAuthenticated) {
        const headers = {};
        if (authStore.token) headers['Authorization'] = `Bearer ${authStore.token}`;
        if (authStore.user?.apiKey) headers['X-API-Key'] = authStore.user.apiKey;

        if (Object.keys(headers).length > 0) {
          await axios.post(
              `${import.meta.env.VITE_API_URL}/history/log`,
              {
                action: 'pdf-export-user-guide',
                description: 'Exported user guide to PDF',
                metadata: {
                  operationType: 'export',
                  timestamp: new Date().toISOString()
                }
              },
              { headers }
          );
        }
      }
    } catch (logError) {
      console.warn('Failed to log PDF export operation:', logError);
    }
  } catch (error) {
    console.error('Error generating PDF:', error);
    alert('Error generating PDF. Please try again later.');
  } finally {
    loading.value = false;
  }
};
</script>
<style scoped>
.guide-section {
  scroll-margin-top: 70px;
}

/* Content container with overflow control */
.content-container {
  max-width: 100%;
  overflow-x: hidden;
  padding: 1.5rem;
}

/* Section content wrapper */
.section-content {
  width: 100%;
  padding-right: 1rem;
}

pre {
  white-space: pre-wrap;
  word-wrap: break-word;
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  font-family: monospace;
}

/* Improved list styling */
.v-card .pa-4 ol,
.content-container ol {
  padding-left: 3rem !important;
  max-width: 100%;
  box-sizing: border-box;
}

.text-body-1 ol,
.text-body-1 ul {
  padding-left: 3rem !important;
  margin-bottom: 1rem;
  max-width: calc(100% - 3rem);
}

.text-body-1 li {
  margin-bottom: 0.5rem;
  max-width: 100%;
  word-wrap: break-word;
}

/* Responsive styles */
@media (max-width: 600px) {
  .content-container {
    padding: 1rem;
  }

  .section-content {
    padding-right: 0.5rem;
  }

  .v-card .pa-4 ol,
  .content-container ol,
  .text-body-1 ol,
  .text-body-1 ul {
    padding-left: 2rem !important;
  }

  .text-body-1 ol,
  .text-body-1 ul {
    max-width: calc(100% - 2rem);
  }
}
</style>