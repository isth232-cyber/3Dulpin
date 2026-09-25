import os
import sys
import pytest
import shutil

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from pipeline.photogrammetry.validation import validate_input_directory
from pipeline.photogrammetry.job import PhotogrammetryJob

def test_m1_input_validation_missing_dir():
    """UNIT TEST: Photogrammetry input validation for missing directory"""
    is_valid, msg, images = validate_input_directory("non_existent_dir_12345")
    assert not is_valid
    assert "does not exist" in msg.lower()

def test_m1_input_validation_empty_dir(tmp_path):
    """UNIT TEST: Photogrammetry input validation for empty directory (Missing images)"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    is_valid, msg, images = validate_input_directory(str(empty_dir))
    assert not is_valid
    assert "insufficient images" in msg.lower()

def test_m1_input_validation_valid_images(tmp_path):
    """UNIT TEST: Photogrammetry input validation for valid images"""
    valid_dir = tmp_path / "valid"
    valid_dir.mkdir()
    
    # Create fake images
    for i in range(5):
        img_path = valid_dir / f"img_{i}.jpg"
        img_path.write_text("fake image data")
        
    is_valid, msg, images = validate_input_directory(str(valid_dir))
    assert is_valid
    assert len(images) == 5

def test_m1_input_validation_duplicates(tmp_path):
    """UNIT TEST: Photogrammetry input validation for duplicate names"""
    dup_dir = tmp_path / "dup"
    dup_dir.mkdir()
    
    # Create duplicate names but different extensions
    (dup_dir / "img1.jpg").write_text("fake")
    (dup_dir / "img1.png").write_text("fake")
    (dup_dir / "img2.jpg").write_text("fake")
    (dup_dir / "img3.jpg").write_text("fake")
    
    is_valid, msg, images = validate_input_directory(str(dup_dir))
    assert not is_valid
    assert "duplicate" in msg.lower()

def test_m1_job_configuration():
    """UNIT TEST: Job configuration"""
    job = PhotogrammetryJob(
        job_id="test_id",
        image_directory="images",
        output_directory="out",
        configuration={"fast_orthophoto": True}
    )
    assert job.status == "INITIALIZED"
    assert job.configuration["fast_orthophoto"] is True
