# model_utils.py
# ---------------------------------------------
# Dummy prediction model (sementara)
# Bisa diganti SVM, HOG, CNN, dsb.
# ---------------------------------------------

def predict_image_stub(pil_image):
    """
    Fungsi ini hanya sebagai dummy.
    Output harus sesuai ID penyakit yang ada di rules.json,
    agar bisa dipakai menggunakan forward chaining.
    """

    # Probabilitas dummy (total tidak harus 1.0)
    return {
        "smut": 0.1,            # Penyakit Gosong Jagung
        "msv": 0.1,             # Maize Streak Virus
        "gls": 0.1,             # Gray Leaf Spot
        "tlb": 0.1,             # Turcicum Leaf Blight
        "ear_rot": 0.1,         # Busuk Tongkol
        "healthy": 0.5          # Daun sehat
    }
