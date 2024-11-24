import React, { useState } from 'react';
import CodeMirror, { ReactCodeMirrorProps } from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import { EditorView } from '@codemirror/view';
import { useTranslation } from 'react-i18next';

interface IProps extends ReactCodeMirrorProps {
  onChange?: (value: string) => void;
}

export default function JsonEditor(props: IProps) {
  const { t, i18n } = useTranslation();
  const [isValidJson, setIsValidJson] = useState(true);
  const [jsonContent, setJsonContent] = useState(props.value);

  // 格式化 JSON 内容
  const formatJson = (code: string) => {
    const parsed = JSON.parse(code);
    const formattedJson =  JSON.stringify(parsed, null, 2);
    return formattedJson
  };
  const handleEditorChange = (value: string) => {
    try {
      const formattedJson = formatJson(value);
      if (props.onChange) {
        props.onChange(formattedJson);
      }
      setIsValidJson(true);
    } catch (e) {
      setIsValidJson(false);
      if (props.onChange) {
        props.onChange(value);
      }
    }
  };

  return (
    <div>
      <CodeMirror
        value={formatJson(jsonContent || '{}')}
        onChange={(value) => handleEditorChange(value)}  // 处理内容变化
        readOnly={props.readOnly}  // 控制只读模式
        height="300px"
        extensions={[
          json(),               // 启用 JSON 语法高亮
          EditorView.lineWrapping, // 启用自动换行
        ]}
        placeholder={props.placeholder}  // 设置占位符
        basicSetup={{ lineNumbers: false }}  // 启用行号
      />
      {/* 显示无效 JSON 提示 */}
      {!isValidJson && (
        <div style={{ color: 'red', marginTop: '10px' }}>
          {t("json格式错误")}
        </div>
      )}
    </div>
  );
}
