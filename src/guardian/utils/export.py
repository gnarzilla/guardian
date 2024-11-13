# src/guardian/utils/export.py
from typing import Any, Dict, Optional
import json
import yaml
import csv
from pathlib import Path
from datetime import datetime
from rich.console import Console
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod

class Exporter(ABC):
    """Base class for exporters"""
    @abstractmethod
    def export(self, data: Dict[str, Any], file_path: Optional[Path] = None) -> str:
        pass

class JSONExporter(Exporter):
    def export(self, data: Dict[str, Any], file_path: Optional[Path] = None) -> str:
        content = json.dumps(data, indent=2)
        if file_path:
            file_path.write_text(content)
        return content

class YAMLExporter(Exporter):
    def export(self, data: Dict[str, Any], file_path: Optional[Path] = None) -> str:
        content = yaml.safe_dump(data, sort_keys=False)
        if file_path:
            file_path.write_text(content)
        return content

class CSVExporter(Exporter):
    def export(self, data: Dict[str, Any], file_path: Optional[Path] = None) -> str:
        # Flatten nested dict for CSV
        flattened = self._flatten_dict(data)
        content = self._dict_to_csv(flattened)
        if file_path:
            file_path.write_text(content)
        return content

    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def _dict_to_csv(self, data: Dict) -> str:
        output = []
        headers = list(data.keys())
        output.append(','.join(f'"{h}"' for h in headers))
        output.append(','.join(f'"{data[h]}"' if data[h] is not None else '' for h in headers))
        return '\n'.join(output)

class XMLExporter(Exporter):
    def export(self, data: Dict[str, Any], file_path: Optional[Path] = None) -> str:
        root = ET.Element("report")
        self._dict_to_xml(data, root)
        content = ET.tostring(root, encoding='unicode', method='xml')
        if file_path:
            file_path.write_text(content)
        return content

    def _dict_to_xml(self, data: Dict[str, Any], parent: ET.Element):
        for key, value in data.items():
            child = ET.SubElement(parent, str(key))
            if isinstance(value, dict):
                self._dict_to_xml(value, child)
            else:
                child.text = str(value)

class ExportManager:
    """Manages data exports in various formats"""
    
    EXPORTERS = {
        'json': JSONExporter(),
        'yaml': YAMLExporter(),
        'csv': CSVExporter(),
        'xml': XMLExporter(),
    }

    @classmethod
    def export(cls, data: Dict[str, Any], format: str = 'yaml', 
               output_dir: Optional[Path] = None) -> str:
        """Export data in specified format"""
        if format not in cls.EXPORTERS:
            raise ValueError(f"Unsupported format: {format}")
        
        exporter = cls.EXPORTERS[format]
        file_path = None
        
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = output_dir / f"report_{timestamp}.{format}"
        
        return exporter.export(data, file_path)
