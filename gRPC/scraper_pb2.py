# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: scraper.proto
# Protobuf Python Version: 4.25.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rscraper.proto\x12\x07scraper\"V\n\x07Request\x12\r\n\x05topic\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\x12\x0e\n\x06sender\x18\x03 \x01(\t\x12\x0c\n\x04time\x18\x04 \x01(\t\x12\r\n\x05match\x18\x05 \x01(\t\"Y\n\x08Response\x12\r\n\x05topic\x18\x01 \x01(\t\x12\x0f\n\x07\x63ontent\x18\x02 \x01(\t\x12\x0f\n\x07success\x18\x03 \x01(\x08\x12\x0e\n\x06source\x18\x04 \x01(\t\x12\x0c\n\x04time\x18\x05 \x01(\t26\n\x07Message\x12+\n\x04Send\x12\x10.scraper.Request\x1a\x11.scraper.Responseb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'scraper_pb2', _globals)
if _descriptor._USE_C_DESCRIPTORS == False:
  DESCRIPTOR._options = None
  _globals['_REQUEST']._serialized_start=26
  _globals['_REQUEST']._serialized_end=112
  _globals['_RESPONSE']._serialized_start=114
  _globals['_RESPONSE']._serialized_end=203
  _globals['_MESSAGE']._serialized_start=205
  _globals['_MESSAGE']._serialized_end=259
# @@protoc_insertion_point(module_scope)
