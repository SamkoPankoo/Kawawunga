import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const usePdfStore = defineStore('pdf', () => {
    const currentPdf = ref(null)
    const pdfData = ref(null)

    async function setCurrentPdf(file) {
        currentPdf.value = file
        // Upload to server
        const formData = new FormData()
        formData.append('pdf', file)

        try {
            const response = await axios.post(`/python-api/upload`, formData)
            pdfData.value = response.data
        } catch (error) {
            console.error('Failed to upload PDF:', error)
        }
    }

    async function rotatePage(pageNumber) {
        try {
            const response = await axios.post(`/python-api/rotate`, {
                file_id: pdfData.value.id,
                page: pageNumber,
                rotation: 90
            })
            pdfData.value = response.data
        } catch (error) {
            console.error('Failed to rotate page:', error)
        }
    }

    async function deletePage(pageNumber) {
        try {
            const response = await axios.post(`/python-api/delete-page`, {
                file_id: pdfData.value.id,
                page: pageNumber
            })
            pdfData.value = response.data
        } catch (error) {
            console.error('Failed to delete page:', error)
        }
    }

    async function mergePdfs(file) {
        const formData = new FormData()
        formData.append('file1', currentPdf.value)
        formData.append('file2', file)

        try {
            const response = await axios.post(`/python-api/merge`, formData)
            pdfData.value = response.data
        } catch (error) {
            console.error('Failed to merge PDFs:', error)
        }
    }

    async function downloadPdf() {
        try {
            const response = await axios.get(`/python-api/download/${pdfData.value.id}`, {
                responseType: 'blob'
            })

            const url = window.URL.createObjectURL(new Blob([response.data]))
            const link = document.createElement('a')
            link.href = url
            link.setAttribute('download', 'edited.pdf')
            document.body.appendChild(link)
            link.click()
            link.remove()
        } catch (error) {
            console.error('Failed to download PDF:', error)
        }
    }

    return {
        currentPdf,
        pdfData,
        setCurrentPdf,
        rotatePage,
        deletePage,
        mergePdfs,
        downloadPdf
    }
})