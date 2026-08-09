import os
from unittest.mock import patch, MagicMock
from app.core.asset_manager import ensure_assets_exist, ASSETS, MODELS_DIR

def test_ensure_assets_exist_all_present(mocker):
    """
    Test when all assets already exist, urlretrieve should not be called.
    """
    # Mock os.path.exists to return True
    mock_exists = mocker.patch("os.path.exists", return_value=True)
    # Mock urllib.request.urlretrieve
    mock_urlretrieve = mocker.patch("urllib.request.urlretrieve")
    # Mock os.makedirs
    mock_makedirs = mocker.patch("os.makedirs")

    ensure_assets_exist()

    # Since they exist, urlretrieve should not be called
    mock_urlretrieve.assert_not_called()
    mock_makedirs.assert_called_once_with(MODELS_DIR, exist_ok=True)

def test_ensure_assets_exist_missing_download(mocker):
    """
    Test when assets do not exist, urlretrieve should download them.
    """
    # Mock os.path.exists to return False
    mock_exists = mocker.patch("os.path.exists", return_value=False)
    # Mock urllib.request.urlretrieve
    mock_urlretrieve = mocker.patch("urllib.request.urlretrieve")
    # Mock os.makedirs
    mock_makedirs = mocker.patch("os.makedirs")

    ensure_assets_exist()

    # urlretrieve should be called for each asset
    assert mock_urlretrieve.call_count == len(ASSETS)
    mock_makedirs.assert_called_once_with(MODELS_DIR, exist_ok=True)

    # Verify download URL and path for each asset
    for filename, url in ASSETS.items():
        expected_path = os.path.join(MODELS_DIR, filename)
        mock_urlretrieve.assert_any_call(url, expected_path)
