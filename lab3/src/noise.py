import os
import numpy as np
from PIL import Image
from pathlib import Path


INPUT_DIR = "input_images"      
OUTPUT_DIR = "test_dataset"     


Path(OUTPUT_DIR).mkdir(exist_ok=True)

def add_gaussian_noise(img, sigma=25):
    
    img_array = np.array(img, dtype=np.float32)
    noise = np.random.normal(0, sigma, img_array.shape)
    noisy = img_array + noise
    return Image.fromarray(np.clip(noisy, 0, 255).astype(np.uint8))

def gaussian_blur(img, kernel_size=15, sigma=3.0):
    
    def gaussian_kernel(size, sigma):
        ax = np.arange(-size // 2 + 1., size // 2 + 1.)
        xx, yy = np.meshgrid(ax, ax)
        kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
        return kernel / np.sum(kernel)
    
    img_array = np.array(img)
    kernel = gaussian_kernel(kernel_size, sigma)
    pad = kernel_size // 2
    if img_array.ndim == 3:
        blurred = np.zeros_like(img_array)
        for c in range(3):
            padded = np.pad(img_array[:, :, c], pad, mode='edge')
            for i in range(img_array.shape[0]):
                for j in range(img_array.shape[1]):
                    blurred[i, j, c] = np.sum(
                        padded[i:i+kernel_size, j:j+kernel_size] * kernel
                    )
    else:
        padded = np.pad(img_array, pad, mode='edge')
        blurred = np.zeros_like(img_array)
        for i in range(img_array.shape[0]):
            for j in range(img_array.shape[1]):
                blurred[i, j] = np.sum(
                    padded[i:i+kernel_size, j:j+kernel_size] * kernel
                )
    return Image.fromarray(np.clip(blurred, 0, 255).astype(np.uint8))

def reduce_contrast(img, factor=0.3):
    
    img_array = np.array(img, dtype=np.float32)
    mean = 128.0
    low_contrast = mean + factor * (img_array - mean)
    return Image.fromarray(np.clip(low_contrast, 0, 255).astype(np.uint8))

def darken_image(img, factor=0.4):
    
    img_array = np.array(img, dtype=np.float32)
    dark = img_array * factor
    return Image.fromarray(np.clip(dark, 0, 255).astype(np.uint8))

def overexpose_image(img, factor=1.8):
    
    img_array = np.array(img, dtype=np.float32)
    over = img_array * factor
    return Image.fromarray(np.clip(over, 0, 255).astype(np.uint8))

def process_image(input_path, output_dir):
    
    try:
        original = Image.open(input_path).convert('RGB')
        name = Path(input_path).stem
        
        
        noisy = add_gaussian_noise(original, sigma=30)
        noisy.save(os.path.join(output_dir, f"{name}_noisy.jpg"))
        
        
        blurred = gaussian_blur(original, kernel_size=15, sigma=2.5)
        blurred.save(os.path.join(output_dir, f"{name}_blurred.jpg"))
        
        
        low_contrast = reduce_contrast(original, factor=0.4)
        low_contrast.save(os.path.join(output_dir, f"{name}_low_contrast.jpg"))
        
        
        dark = darken_image(original, factor=0.3)
        dark.save(os.path.join(output_dir, f"{name}_dark.jpg"))
        
        
        over = overexpose_image(original, factor=2.0)
        over.save(os.path.join(output_dir, f"{name}_overexposed.jpg"))
        
        print(f"✅ Апрацавана: {name}")
    except Exception as e:
        print(f"❌ Памылка пры апрацоўцы {input_path}: {e}")

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Папка {INPUT_DIR} не існуе! Стварыце яе і дадайце выявы.")
        return
    
    image_files = []
    for ext in ["*.jpg", "*.jpeg", "*.png", "*.bmp"]:
        image_files.extend(Path(INPUT_DIR).glob(ext))
    
    if not image_files:
        print(f"Няма выяў у {INPUT_DIR}! Дадайце файлы з пашырэннямі: jpg, png, bmp.")
        return
    
    print(f"Знойдзена {len(image_files)} выяў. Пачынаю стварэнне тэставай базы...")
    
    for img_path in image_files:
        process_image(str(img_path), OUTPUT_DIR)
    
    print(f"\n🎉 Гатова! Тэставая база захавана ў папку: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()