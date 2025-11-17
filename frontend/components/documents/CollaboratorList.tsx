"use client";

import { useEffect, useState } from "react";
import { documentApi } from "@/lib/api";
import type { DocumentCollaborator } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Users, UserPlus, Trash2, Eye, Edit } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { useAuth } from "@/contexts/AuthContext";
import { getUserColor } from "@/lib/utils/colors";

interface CollaboratorListProps {
  documentId: string;
  onInviteClick: () => void;
}

export function CollaboratorList({
  documentId,
  onInviteClick,
}: CollaboratorListProps) {
  const { user } = useAuth();
  const [collaborators, setCollaborators] = useState<DocumentCollaborator[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCollaborators();
  }, [documentId]);

  const loadCollaborators = async () => {
    try {
      setLoading(true);
      const result = await documentApi.getCollaborators(documentId);
      setCollaborators(result);
    } catch (error) {
      console.error("Failed to load collaborators:", error);
    } finally {
      setLoading(false);
    }
  };

  const getInitials = (email: string) => {
    const parts = email.split("@")[0].split(".");
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return email.substring(0, 2).toUpperCase();
  };

  const isCurrentUser = (collaborator: DocumentCollaborator) => {
    return user && collaborator.user_id === user.id;
  };

  if (loading) {
    return (
      <div className="flex items-center gap-2">
        <div className="h-8 w-8 rounded-full bg-gray-200 animate-pulse" />
        <div className="h-8 w-8 rounded-full bg-gray-200 animate-pulse" />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      {/* Avatar Stack */}
      <div className="flex items-center -space-x-2">
        {collaborators.slice(0, 5).map((collaborator) => {
          const userColor = getUserColor(collaborator.user_id);
          return (
            <Avatar
              key={collaborator.id}
              className="border-2 border-white"
              style={{
                backgroundColor: userColor,
              }}
              title={`${collaborator.user?.email || "Unknown"} (${
                collaborator.permission
              })`}
            >
              <AvatarFallback
                className="text-white font-semibold text-xs"
                style={{
                  backgroundColor: userColor,
                }}
              >
                {collaborator.user?.email
                  ? getInitials(collaborator.user.email)
                  : "?"}
              </AvatarFallback>
            </Avatar>
          );
        })}
        {collaborators.length > 5 && (
          <div
            className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center text-xs font-semibold text-gray-700 border-2 border-white"
            title={`+${collaborators.length - 5} more`}
          >
            +{collaborators.length - 5}
          </div>
        )}
      </div>

      {/* Collaborators Dropdown */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            <Users className="h-4 w-4" />
            {collaborators.length}
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-80">
          <div className="px-2 py-2 border-b">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-sm">Collaborators</h3>
              <Button
                size="sm"
                variant="ghost"
                onClick={onInviteClick}
                className="h-7 gap-1"
              >
                <UserPlus className="h-3 w-3" />
                Invite
              </Button>
            </div>
          </div>

          <div className="max-h-[300px] overflow-y-auto">
            {collaborators.map((collaborator) => {
              const userColor = getUserColor(collaborator.user_id);
              const currentUser = isCurrentUser(collaborator);

              return (
                <div
                  key={collaborator.id}
                  className="px-2 py-2 hover:bg-gray-50 flex items-center justify-between"
                >
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <Avatar
                      className="h-8 w-8 flex-shrink-0"
                      style={{
                        backgroundColor: userColor,
                      }}
                    >
                      <AvatarFallback
                        className="text-white font-semibold text-xs"
                        style={{
                          backgroundColor: userColor,
                        }}
                      >
                        {collaborator.user?.email
                          ? getInitials(collaborator.user.email)
                          : "?"}
                      </AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium truncate">
                          {collaborator.user?.email || "Unknown"}
                        </p>
                        {currentUser && (
                          <Badge variant="secondary" className="text-xs">
                            You
                          </Badge>
                        )}
                      </div>
                      <div className="flex items-center gap-1 text-xs text-gray-500">
                        {collaborator.permission === "edit" ? (
                          <>
                            <Edit className="h-3 w-3" />
                            Can edit
                          </>
                        ) : (
                          <>
                            <Eye className="h-3 w-3" />
                            Can view
                          </>
                        )}
                      </div>
                    </div>
                  </div>

                  {!currentUser && (
                    <Button
                      size="sm"
                      variant="ghost"
                      className="h-7 w-7 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                      title="Remove collaborator"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </DropdownMenuContent>
      </DropdownMenu>
    </div>
  );
}
