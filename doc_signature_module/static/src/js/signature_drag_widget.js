/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useRef, useState, onMounted } from "@odoo/owl";

export class SignatureDragWidget extends Component {
    static template = "doc_signature_module.SignaturePreviewWidget";
    static props = ["record"];

    setup() {
        this.previewBox = useRef("previewBox");
        this.signatureImg = useRef("signatureImg");
        
        // حالة المكون: الإحداثيات الحالية
        this.state = useState({
            signatureLeft: this.props.record.data.signature_left || 50,
            signatureTop: this.props.record.data.signature_top || 200,
        });

        // متغيرات السحب
        this.isDragging = false;
        this.startX = 0;
        this.startY = 0;
        this.startLeft = 0;
        this.startTop = 0;

        // ربط أحداث الماوس العالمية
        onMounted(() => {
            document.addEventListener("mousemove", this.onDrag.bind(this));
            document.addEventListener("mouseup", this.onDragEnd.bind(this));
        });
    }

    // بدء السحب عند الضغط على الصورة
    onDragStart(ev) {
        ev.preventDefault();
        this.isDragging = true;
        
        // حفظ نقطة البداية
        this.startX = ev.clientX;
        this.startY = ev.clientY;
        this.startLeft = this.state.signatureLeft;
        this.startTop = this.state.signatureTop;
        
        // تغيير شكل المؤشر
        if (this.signatureImg.el) {
            this.signatureImg.el.style.cursor = "grabbing";
        }
    }

    // أثناء حركة الماوس: تحديث الموقع
    onDrag(ev) {
        if (!this.isDragging || !this.previewBox.el) return;
        
        // حساب الإزاحة بالبكسل
        const dx = ev.clientX - this.startX;
        const dy = ev.clientY - this.startY;
        
        // تحويل البكسل إلى مليمتر (تقريبي: 1mm ≈ 3.78px على شاشات 96DPI)
        const mmPerPx = 1 / 3.78;
        
        // تحديث الإحداثيات مع حدود الصفحة (210mm عرض - هوامش)
        let newLeft = this.startLeft + (dx * mmPerPx);
        let newTop = this.startTop + (dy * mmPerPx);
        
        // منع الخروج عن حدود الصفحة
        newLeft = Math.max(0, Math.min(170, newLeft)); // 210mm - 40mm هوامش
        newTop = Math.max(0, Math.min(250, newTop));   // 297mm - 47mm هوامش
        
        // تحديث الحالة (تسبب إعادة رسم فورية)
        this.state.signatureLeft = Math.round(newLeft * 10) / 10; // تقريب لعشرة
        this.state.signatureTop = Math.round(newTop * 10) / 10;
    }

    // إنهاء السحب: حفظ القيم في نموذج أودو
    onDragEnd() {
        if (!this.isDragging) return;
        this.isDragging = false;
        
        if (this.signatureImg.el) {
            this.signatureImg.el.style.cursor = "grab";
        }
        
        // تحديث حقول النموذج فعليًا (سيُحفظ عند ضغط Save)
        this.props.record.update({
            signature_left: this.state.signatureLeft,
            signature_top: this.state.signatureTop,
        });
    }

    // Getter للوصول السهل للحالة في القالب
    get signatureLeft() {
        return this.state.signatureLeft;
    }
    get signatureTop() {
        return this.state.signatureTop;
    }
}

// تسجيل الـ Widget في نظام أودو
registry.category("fields").add("signature_drag_preview", SignatureDragWidget);