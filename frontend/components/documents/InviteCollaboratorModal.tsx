"use client";

import { useState } from "react";
import { documentApi } from "@/lib/api";
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
import { Loader2, AlertCircle, UserPlus } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface InviteCollaboratorModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  documentId: string;
  documentTitle: string;
}

export function InviteCollaboratorModal({
  open,
  onClose,
  onSuccess,
  documentId,
  documentTitle,
}: InviteCollaboratorModalProps) {
  const [userEmail, setUserEmail] = useState("");
  const [permission, setPermission] = useState<"edit" | "view">("edit");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!userEmail.trim()) {
      setError("Please enter an email address");
      return;
    }

    try {
      setLoading(true);

      // First, look up the user by email to get their ID
      // For now, we'll just send the email and let the backend handle it
      await documentApi.addCollaborator(documentId, {
        user_id: userEmail, // Backend should accept email too
        permission,
      });

      // Reset form
      setUserEmail("");
      setPermission("edit");
      onSuccess();
    } catch (err: any) {
      setError(err.message || "Failed to invite collaborator");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setUserEmail("");
      setPermission("edit");
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5" />
            Invite Collaborator
          </DialogTitle>
          <DialogDescription>
            Invite someone to collaborate on "{documentTitle}". They will be able to
            edit the document in real-time.
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
            <Label htmlFor="userEmail">
              Email Address <span className="text-red-500">*</span>
            </Label>
            <Input
              id="userEmail"
              type="email"
              placeholder="colleague@company.com"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
              disabled={loading}
              required
              autoFocus
            />
            <p className="text-sm text-gray-500">
              Email of the person you want to invite
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="permission">
              Permission Level
            </Label>
            <Select
              value={permission}
              onValueChange={(value: "edit" | "view") => setPermission(value)}
              disabled={loading}
            >
              <SelectTrigger id="permission">
                <SelectValue placeholder="Select permission" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="edit">
                  <div className="flex flex-col items-start">
                    <span className="font-medium">Can Edit</span>
                    <span className="text-xs text-gray-500">
                      View and make changes to the document
                    </span>
                  </div>
                </SelectItem>
                <SelectItem value="view">
                  <div className="flex flex-col items-start">
                    <span className="font-medium">Can View</span>
                    <span className="text-xs text-gray-500">
                      View document but cannot make changes
                    </span>
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
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
                  Inviting...
                </>
              ) : (
                <>
                  <UserPlus className="mr-2 h-4 w-4" />
                  Send Invitation
                </>
              )}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
