"use client";

import { useRef, useEffect, useState } from "react";
import SignaturePadLib from "signature_pad";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { PenTool, Type, RotateCcw, Check, X } from "lucide-react";

interface SignaturePadProps {
  onSign: (signature: SignatureData) => void;
  onCancel: () => void;
  signerName?: string;
  signerEmail?: string;
}

export interface SignatureData {
  signature_data: string;
  signature_type: "drawn" | "typed";
  signer_name: string;
}

const SIGNATURE_FONTS = [
  { name: "Cursive", style: "cursive" },
  { name: "Script", style: "'Brush Script MT', cursive" },
  { name: "Elegant", style: "'Lucida Handwriting', cursive" },
  { name: "Classic", style: "'Times New Roman', serif" },
  { name: "Modern", style: "'Arial', sans-serif" },
];

export function SignaturePad({
  onSign,
  onCancel,
  signerName = "",
  signerEmail = "",
}: SignaturePadProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const signaturePadRef = useRef<SignaturePadLib | null>(null);

  const [activeTab, setActiveTab] = useState<"draw" | "type">("draw");
  const [typedName, setTypedName] = useState(signerName);
  const [selectedFont, setSelectedFont] = useState(SIGNATURE_FONTS[0].style);
  const [isDrawn, setIsDrawn] = useState(false);

  useEffect(() => {
    if (canvasRef.current && activeTab === "draw") {
      const signaturePad = new SignaturePadLib(canvasRef.current, {
        backgroundColor: "rgb(255, 255, 255)",
        penColor: "rgb(0, 0, 0)",
      });

      // Resize canvas to fit container
      const resizeCanvas = () => {
        const canvas = canvasRef.current;
        if (canvas) {
          const ratio = Math.max(window.devicePixelRatio || 1, 1);
          const rect = canvas.getBoundingClientRect();
          canvas.width = rect.width * ratio;
          canvas.height = rect.height * ratio;
          canvas.getContext("2d")?.scale(ratio, ratio);
          signaturePad.clear();
        }
      };

      resizeCanvas();
      window.addEventListener("resize", resizeCanvas);

      // Track if signature has been drawn
      signaturePad.addEventListener("endStroke", () => {
        setIsDrawn(true);
      });

      signaturePadRef.current = signaturePad;

      return () => {
        window.removeEventListener("resize", resizeCanvas);
        signaturePad.off();
      };
    }
  }, [activeTab]);

  const handleClear = () => {
    if (signaturePadRef.current) {
      signaturePadRef.current.clear();
      setIsDrawn(false);
    }
  };

  const handleSign = () => {
    let signatureData: string;
    let signatureType: "drawn" | "typed";

    if (activeTab === "draw") {
      if (!signaturePadRef.current || signaturePadRef.current.isEmpty()) {
        alert("Please draw your signature");
        return;
      }
      signatureData = signaturePadRef.current.toDataURL("image/png");
      signatureType = "drawn";
    } else {
      if (!typedName.trim()) {
        alert("Please type your name");
        return;
      }

      // Create canvas for typed signature
      const canvas = document.createElement("canvas");
      canvas.width = 400;
      canvas.height = 150;
      const ctx = canvas.getContext("2d");

      if (ctx) {
        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = "black";
        ctx.font = `48px ${selectedFont}`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(typedName, canvas.width / 2, canvas.height / 2);
      }

      signatureData = canvas.toDataURL("image/png");
      signatureType = "typed";
    }

    onSign({
      signature_data: signatureData,
      signature_type: signatureType,
      signer_name: typedName || signerName,
    });
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Sign Document</CardTitle>
        <CardDescription>
          Draw or type your signature below
          {signerEmail && <span className="block mt-1">Signing as: {signerEmail}</span>}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "draw" | "type")}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="draw">
              <PenTool className="h-4 w-4 mr-2" />
              Draw
            </TabsTrigger>
            <TabsTrigger value="type">
              <Type className="h-4 w-4 mr-2" />
              Type
            </TabsTrigger>
          </TabsList>

          <TabsContent value="draw" className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-2 bg-white">
              <canvas
                ref={canvasRef}
                className="w-full h-48 cursor-crosshair touch-none"
                style={{ touchAction: "none" }}
              />
            </div>
            <div className="flex justify-between">
              <Button
                type="button"
                variant="outline"
                onClick={handleClear}
                disabled={!isDrawn}
              >
                <RotateCcw className="h-4 w-4 mr-2" />
                Clear
              </Button>
              <div className="text-sm text-gray-500">
                Draw your signature above
              </div>
            </div>
          </TabsContent>

          <TabsContent value="type" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="typed-name">Your Name</Label>
              <Input
                id="typed-name"
                type="text"
                value={typedName}
                onChange={(e) => setTypedName(e.target.value)}
                placeholder="Enter your full name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="font-select">Signature Style</Label>
              <Select value={selectedFont} onValueChange={setSelectedFont}>
                <SelectTrigger id="font-select">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SIGNATURE_FONTS.map((font) => (
                    <SelectItem key={font.style} value={font.style}>
                      <span style={{ fontFamily: font.style }}>{font.name}</span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {typedName && (
              <div className="border-2 border-gray-200 rounded-lg p-8 bg-white">
                <div
                  className="text-4xl text-center"
                  style={{ fontFamily: selectedFont }}
                >
                  {typedName}
                </div>
              </div>
            )}
          </TabsContent>
        </Tabs>

        <div className="flex justify-end gap-2 mt-6">
          <Button type="button" variant="outline" onClick={onCancel}>
            <X className="h-4 w-4 mr-2" />
            Cancel
          </Button>
          <Button
            type="button"
            onClick={handleSign}
            disabled={activeTab === "draw" ? !isDrawn : !typedName.trim()}
          >
            <Check className="h-4 w-4 mr-2" />
            Sign Document
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}