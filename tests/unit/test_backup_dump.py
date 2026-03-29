import os
import zipfile
from unittest.mock import patch, MagicMock
from app.routes.backup import trigger_dump
from app import create_app

app = create_app()

def test_zip_creation_2025():
    with app.app_context():
        with app.test_request_context('/export/2025'):
            with patch('app.routes.backup.db.session.scalars') as mock_scalars:
                mock_result = MagicMock()
                mock_result.fetchall.return_value = [
                    "Fichtwald-20250119113000-1fb0cfb0be3b0c75c537a50c57e0060ba8b6837e.webp"
                ]
                mock_scalars.return_value = mock_result

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock()
                    
                    with patch('app.routes.backup.zipfile.ZipFile') as mock_zip:
                        mock_zip_instance = MagicMock()
                        mock_zip.return_value.__enter__.return_value = mock_zip_instance
                        
                        with patch('os.path.isfile') as mock_isfile:
                            mock_isfile.return_value = True
                            
                            # Mock pg_dump Datei
                            with patch('builtins.open', new_callable=MagicMock) as mock_open:
                                mock_open.return_value.__enter__.return_value = MagicMock()
                                
                                # Funktion aufrufen
                                result = trigger_dump(2025)
                                assert result == "2025 gesichert"
