"use client";

import { useState } from "react";
import { negotiationApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, AlertCircle } from "lucide-react";

interface NegotiationRequestModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function NegotiationRequestModal({
  open,
  onClose,
  onSuccess,
}: NegotiationRequestModalProps) {
  const [receiverEmail, setReceiverEmail] = useState("");
  const [contractName, setContractName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!receiverEmail.trim() || !contractName.trim()) {
      setError("Please fill in all required fields");
      return;
    }

    try {
      setLoading(true);
      await negotiationApi.createNegotiation({
        receiver_email: receiverEmail,
        contract_name: contractName,
      });

      // Reset form
      setReceiverEmail("");
      setContractName("");
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to create negotiation request");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setReceiverEmail("");
      setContractName("");
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Start New Negotiation</DialogTitle>
          <DialogDescription>
            Send a negotiation request to another company. They will need to accept
            before you can start chatting.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-2">
            <Label htmlFor="receiverEmail">
              Receiver Email <span className="text-red-500">*</span>
            </Label>
            <Input
              id="receiverEmail"
              type="email"
              placeholder="partner@company.com"
              value={receiverEmail}
              onChange={(e) => setReceiverEmail(e.target.value)}
              disabled={loading}
              required
            />
            <p className="text-sm text-gray-500">
              Email of the person you want to negotiate with
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="contractName">
              Contract Name <span className="text-red-500">*</span>
            </Label>
            <Input
              id="contractName"
              type="text"
              placeholder="Service Agreement, NDA, etc."
              value={contractName}
              onChange={(e) => setContractName(e.target.value)}
              disabled={loading}
              required
            />
            <p className="text-sm text-gray-500">
              Name to identify this negotiation
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={handleClose}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending...
                </>
              ) : (
                "Send Request"
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
