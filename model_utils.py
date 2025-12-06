# model_utils.py
# Placeholder model prediction (jika belum ada model)
# Mengembalikan nilai probabilitas dummy

def predict_image_stub(pil_image):
    """
    Fungsi ini hanya sebagai dummy.
    Jika nanti Anda punya model SVM/HOG atau CNN,
    tinggal ganti implementasinya.
    """
    return {
        "smut": 0.1,
        "msv": 0.1,
        "gray_leaf_spot": 0.1,
        "tlb": 0.1,
        "ear_rot": 0.1,
        "healthy": 0.5
    }
